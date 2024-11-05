import { status } from "../stores";
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
