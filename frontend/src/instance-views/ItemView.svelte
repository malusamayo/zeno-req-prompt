<script lang="ts">
	import { columnHash } from "../util/util";
	import {
		currentPromptId,
		model,
		requirements,
		requirementUpdating,
		settings,
		status,
		promptToUpdate,
		suggestedRequirements,
	} from "../stores";
	import { ZenoColumnType, ZenoService } from "../zenoservice";
	import { clickOutside } from "../util/clickOutside";
	import RequirementEvalChip from "../metadata/chips/RequirementEvalChip.svelte";
	import { TrailingIcon, LeadingIcon } from "@smui/chips";
	import Paper, { Content } from "@smui/paper";
	import { Icon } from "@smui/button";
	import { InitialFocus } from "@smui/dialog";
	import type { Example } from "../zenoservice/models/prompt";
	import RequirementCell from "../metadata/cells/RequirementCell.svelte";
	import UpdateRequirementCell from "../metadata/cells/UpdateRequirementCell.svelte";

	export let item;
	let modelColumn;
	let evalColumns;
	let rationaleColumns;
	let example: Example;

	let requirementIds;

	let showFeedback = false;
	let feedbackThumbUp;
	let feedbackText = "";
	let showOptions = false;
	let newRequirementInput = "";
	let showRequirementModal = false;
	let showExistingRequirementModal = false;

	$: {
		$model;
		$currentPromptId;
		$status;

		let obj = $status.completeColumns.find((c) => {
			return (
				c.columnType === ZenoColumnType.OUTPUT &&
				c.model === $model &&
				c.promptId === $currentPromptId
			);
		});
		modelColumn = obj ? columnHash(obj) : "";

		evalColumns = $status.completeColumns
			.filter((c) => {
				return (
					c.columnType === ZenoColumnType.POSTDISTILL &&
					c.model === $model &&
					c.promptId === $currentPromptId &&
					!c.name.includes("Rationale")
				);
			})
			.reduce((acc, col) => {
				let reqId = col.name.replace("evalR", "");
				return { ...acc, [reqId]: columnHash(col) };
			}, {});

		rationaleColumns = $status.completeColumns
			.filter((c) => {
				return (
					c.columnType === ZenoColumnType.POSTDISTILL &&
					c.model === $model &&
					c.promptId === $currentPromptId &&
					c.name.includes("Rationale")
				);
			})
			.reduce((acc, col) => {
				let reqId = col.name.replace("evalR", "").replace("Rationale", "");
				return { ...acc, [reqId]: columnHash(col) };
			}, {});

		requirementIds = Object.keys($requirements);

		example = <Example>{
			id: item[columnHash($settings.idColumn)],
			input: item[columnHash($settings.dataColumn)],
			output: modelColumn ? item[modelColumn] : "",
			isPositive: true,
			feedback: "",
		};
	}

	function runPrompt() {
		status.update((s) => {
			s.status = "Running inference";
			return s;
		});
		ZenoService.runPrompt({
			model: $model,
			promptId: $currentPromptId,
			filterIds: { ids: [item[columnHash($settings.idColumn)]] },
		}).then(() => {
			ZenoService.getCompleteColumns().then((cols) => {
				status.update((s) => {
					s.status = "Done processing";
					s.completeColumns = cols;
					return s;
				});
			});
		});
	}

	// function feedbackToRequirements() {
	// 	requirementUpdating.set(true);
	// 	ZenoService.suggestRequirementUpdates({
	// 		model: $model,
	// 		promptId: $currentPromptId,
	// 		exampleId: item[columnHash($settings.idColumn)],
	// 		isPositive: feedbackThumbUp,
	// 		feedback: feedbackText,
	// 	}).then((newRequirements) => {
	// 		suggestedRequirements.set(newRequirements);
	// 		showFeedback = false;
	// 		feedbackText = "";
	// 		requirementUpdating.set(false);
	// 	});
	// }
	
	function get_max_requirement_id() {
		return Math.max(
			Math.max(...Object.keys($requirements).map((id) => Number(id))),
			0
		);
	}

	function add_requirement() {
		let requirement = {
			id: (get_max_requirement_id() + 1).toString(),
			name: "",
			description: newRequirementInput,
			promptSnippet: "",
			evaluationMethod: "",
		};

		requirementUpdating.set(true);
		ZenoService.optimizeRequirement([requirement]).then(
			(optimizedRequirement) => {
				requirement = optimizedRequirement;
				requirements.update(($reqs) => {
					$reqs[requirement.id] = requirement;
					return $reqs;
				});
				promptToUpdate.set(true);
				newRequirementInput = "";
				requirementUpdating.set(false);
				showRequirementModal = false;
			}
		);
	}

	// function feedbackToEvaluators(eval_res, reqId) {
	// 	requirementUpdating.set(true);
	// 	ZenoService.evaluatorUpdates({
	// 		model: $model,
	// 		promptId: $currentPromptId,
	// 		exampleId: item[columnHash($settings.idColumn)],
	// 		corrected_eval: !eval_res,
	// 		requirementId: reqId,
	// 	}).then((newRequirements) => {
	// 		requirements.set(newRequirements);
	// 		requirementUpdating.set(false);
	// 	});
	// }

	// function submit(e) {
	// 	if (e.metaKey && e.key === "Enter") {
	// 		e.preventDefault();
	// 		feedbackToRequirements();
	// 	}
	// }
</script>

<div
	class="box svelte-ohpquu"
	draggable="false"
	on:dragstart={(ev) => {
		let transferData = JSON.stringify(example);
		ev.dataTransfer.setData("text/plain", transferData);
		ev.dataTransfer.dropEffect = "copy";
	}}>
	<span class="label svelte-ohpquu">input:</span>
	<span class="value svelte-ohpquu">
		{item[columnHash($settings.dataColumn)]}
	</span>
	<TrailingIcon
		class="material-icons"
		style="margin-bottom: 5px; margin-left: 0px; cursor: pointer; opacity: 0.8;"
		on:click={() => {
			runPrompt();
		}}>
		play_circle
	</TrailingIcon>
	{#if modelColumn !== "" && item[modelColumn] !== null}
		<br />
		<span class="label svelte-ohpquu">output:</span>
		<span class="value svelte-ohpquu">
			{item[modelColumn]}
		</span>
		<span style="position:relative">
			<TrailingIcon
				class="material-icons"
				style="margin-bottom: 5px; margin-left: 0px; cursor: pointer; color: #97ca00;"
				on:click={() => {
					// showFeedback = !showFeedback;
					feedbackThumbUp = true;
					showExistingRequirementModal = true;
				}}>
				thumb_up
			</TrailingIcon>
			<TrailingIcon
				class="material-icons"
				style="margin-bottom: 5px; margin-left: 3px; cursor: pointer; color: #e05d44;"
				on:click={() => {
					// showFeedback = !showFeedback;
					feedbackThumbUp = false;
					showOptions = !showOptions;
				}}>
				thumb_down
			</TrailingIcon>
			<!-- {#if showFeedback}
				<div
					id="options-container"
					use:clickOutside
					on:click_outside={(e) => {
						e.preventDefault();
						showFeedback = false;
					}}>
					<Paper style="padding: 3px 0px;" elevation={7}>
						<div class="feedback-box">
							<textarea
								bind:value={feedbackText}
								placeholder="Provide optional feedback here. ⌘ + Enter to submit."
								on:keydown={submit}
								autofocus />
						</div>
					</Paper>
				</div>
			{/if} -->
			{#if showOptions}
				<div class="options" style="position: absolute; bottom: 20px; left: 5px;">
					<TrailingIcon
						class="material-icons small-icon"
						style="cursor: pointer; color: #e05d44;"
						on:click={() => {
							showOptions = false;
							showRequirementModal = true;
						}}>
						error
					</TrailingIcon>
					<TrailingIcon
						class="material-icons small-icon"
						style="cursor: pointer; color: #e05d44;"
						on:click={() => {
							showOptions = false;
							showExistingRequirementModal = true;
						}}>
						feedback
					</TrailingIcon>
				</div>
			{/if}
			{#if showRequirementModal}
			<div class="modal">
				<div class="modal-content">
					<h3>Add New Requirement</h3>
					<textarea
						bind:value={newRequirementInput}
						placeholder="Type a description for the new requirement..." />
					<div class="modal-actions">
						<button on:click={add_requirement}>Add Requirement</button>
						<button on:click={() => showRequirementModal = false}>Cancel</button>
					</div>
				</div>
			</div>
			{/if}
			{#if showExistingRequirementModal}
			<div class="modal">
				<div class="modal-content">
					<h3>Current Requirements</h3>
					<div class="requirement-list">
						{#each Object.entries($requirements) as [id, req]}
							<UpdateRequirementCell
								requirement={req}
								exampleId={item[columnHash($settings.idColumn)]}
								feedbackPositive={feedbackThumbUp} />
						{/each}
					</div>
					<div class="modal-actions">
						<button on:click={() => showExistingRequirementModal = false}>Close</button>
					</div>
				</div>
			</div>
		{/if}
		</span>
	{/if}
	{#if Object.keys(evalColumns).length > 0}
		<br />
		{#each requirementIds as reqId}
			{#if evalColumns[reqId] !== "" && item[evalColumns[reqId]] !== null}
				<RequirementEvalChip
					id={reqId}
					isPass={item[evalColumns[reqId]] === true}
					rationale={item[rationaleColumns[reqId]]}
					item ={item}
					evalColumns={evalColumns}
					reqId={reqId}/>
			{/if}
		{/each}
	{/if}
</div>

<style>
	.label.svelte-ohpquu {
		font-size: 12px;
		color: rgba(0, 0, 0, 0.5);
		font-variant: small-caps;
	}
	.value.svelte-ohpquu {
		font-size: 12px;
		white-space: pre-wrap;
	}
	.box.svelte-ohpquu {
		padding: 10px;
		border: 0.5px solid rgb(224, 224, 224);
		margin: 1px;
	}

	#options-container {
		top: 20px;
		left: 0px;
		z-index: 5;
		position: absolute;
	}
	.feedback-box {
		margin: 5px;
	}

	textarea {
		position: relative;
		overflow: visible;
		border: 0.5px solid var(--G4);
		border-radius: 4px;
		margin-top: 5px;
		display: flex;
		padding-left: 5px;
		padding-right: 10px;
		min-height: 36px;
		min-width: 200px;
		font-size: small;
		font-weight: lighter;
		resize: none;
	}
	.options {
		display: flex;
		flex-direction: row; /* Horizontally aligns the icons */
		gap: 5px; /* Adds spacing between icons */
	}
	.modal {
		position: fixed;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 400px;
		padding: 20px;
		background-color: white;
		border: 1px solid #ccc;
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
		z-index: 100;
	}

	.modal-content {
		display: flex;
		flex-direction: column;
	}

	.modal-actions {
		display: flex;
		justify-content: space-between;
		margin-top: 10px;
	}

	.requirement-list {
		max-height: 300px;
		overflow-y: auto;
		margin-bottom: 10px;
	}
</style>
