import { get } from "svelte/store";
import {
	currentPromptId,
	model,
	prompts,
	promptToUpdate,
	promptUpdating,
	status,
	suggestedRequirements,
} from "../stores";
import { ZenoService } from "../zenoservice/";

export async function runPrompt(model, promptId, filterIds?) {
	status.update((s) => {
		s.status = "Running inference";
		return s;
	});
	ZenoService.runPrompt({
		model: model,
		promptId: promptId,
		filterIds: filterIds,
	}).then(() => {
		ZenoService.getCompleteColumns().then((cols) => {
			status.update((s) => {
				s.status = "Running evaluators";
				s.completeColumns = cols;
				return s;
			});
			ZenoService.runEvaluation({
				model: model,
				promptId: promptId,
				filterIds: filterIds,
			}).then(() => {
				ZenoService.getCompleteColumns().then((cols) => {
					status.update((s) => {
						s.status = "Done processing";
						s.completeColumns = cols;
						return s;
					});
				});
			});
		});
	});
}

export async function compilePrompt(requirements, task, compileOnly?: boolean) {
	promptUpdating.set(true);
	suggestedRequirements.set({});
	status.update((s) => {
		s.status = "Compiling requirements";
		return s;
	});
	ZenoService.createNewPrompt({
		text: "",
		version: "",
		requirements: requirements,
		task: task,
	}).then((createdPrompts) => {
		prompts.update((pts) => {
			return pts.set(createdPrompts[0].version, createdPrompts[0]);
		});
		currentPromptId.set(createdPrompts[0].version);
		promptUpdating.set(false);
		promptToUpdate.set(false);
		if (!compileOnly) {
			runPrompt(get(model), get(currentPromptId));
		} else {
			ZenoService.getCompleteColumns().then((cols) => {
				status.update((s) => {
					s.status = "Done processing";
					s.completeColumns = cols;
					return s;
				});
			});
		}
	});
}
