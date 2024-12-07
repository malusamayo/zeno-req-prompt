<script lang="ts">
	import { columnHash } from "../util/util";
	import {
		currentPromptId,
		comparePromptId,
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
	import { runPrompt } from "../api/prompt";
	import { onMount } from "svelte";
	import { loop_guard } from "svelte/internal";

	export let item;
	export let item_compare;
	let modelColumn;
	let modelColumn_compare;
	let evalColumns;
	let evalColumns_compare;
	let rationaleColumns;
	let example: Example;

	let requirementIds;

	let showFeedback = false;
	let feedbackThumbUp = false;
	let feedbackText = "";
	let showOptions = false;
	let newRequirementInput = "";
	let showRequirementModal = false;
	let showExistingRequirementModal = false;

	let isDraggable = true;

	$: {
		$model;
		$currentPromptId;
		$status;
		$comparePromptId;

		let obj = $status.completeColumns.find((c) => {
			return (
				c.columnType === ZenoColumnType.OUTPUT &&
				c.model === $model &&
				c.promptId === $currentPromptId
			);
		});

		let obj_compare = $status.completeColumns.find((c) => {
			return (
				c.columnType === ZenoColumnType.OUTPUT &&
				c.model === $model &&
				c.promptId === $comparePromptId
			);
		});

		modelColumn = obj ? columnHash(obj) : "";
		modelColumn_compare = obj_compare ? columnHash(obj_compare) : "";

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

		evalColumns_compare = $status.completeColumns
			.filter((c) => {
				return (
					c.columnType === ZenoColumnType.POSTDISTILL &&
					c.model === $model &&
					c.promptId === $comparePromptId &&
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
			id: String(item[columnHash($settings.idColumn)]),
			input: item[columnHash($settings.dataColumn)],
			output: modelColumn ? item[modelColumn] : "",
			isPositive: true,
			feedback: "",
		};
	}

	$: passFailInfo = requirementIds.reduce((acc, reqId) => {
		acc[reqId] = item[evalColumns[reqId]] === true;
		return acc;
	}, {});


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
		let feedback;

		if (feedbackThumbUp === true) {
			feedback =
				"This is a positive example for this requirement affirmed by users";
		} else if (feedbackThumbUp === false) {
			feedback =
				"This is a negative example for this requirement affirmed by users";
		}
		let requirement = {
			id: (get_max_requirement_id() + 1).toString(),
			name: "",
			description: newRequirementInput,
			promptSnippet: "",
			evaluationMethod: "",
			examples: [
				<Example>{
					id: item[columnHash($settings.idColumn)],
					input: item[columnHash($settings.dataColumn)],
					output: modelColumn ? item[modelColumn] : "",
					isPositive: feedbackThumbUp,
					feedback: feedback,
				},
			],
		};

		requirementUpdating.set(true);
		ZenoService.optimizeRequirement({
			promptId: $currentPromptId,
			requirement: requirement,
		}).then((optimizedRequirement) => {
			requirement = optimizedRequirement;
			requirements.update(($reqs) => {
				$reqs[requirement.id] = requirement;
				return $reqs;
			});
			newRequirementInput = "";
			promptToUpdate.set(true);
			requirementUpdating.set(false);
			// showRequirementModal = false;
		});
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

	let menuX = 0;
	let menuY = 0;

	function updateModalPosition(event) {
		const iconRect = event.target.getBoundingClientRect();
		menuX = iconRect.left + window.scrollX;
		menuY = iconRect.bottom + window.scrollY;
	}

	function handleThumbUpClick(event) {
		feedbackThumbUp = true;
		// showExistingRequirementModal = true;
		showOptions = !showOptions;
		updateModalPosition(event);
	}

	function handleThumbDownClick(event) {
		feedbackThumbUp = false;
		showOptions = !showOptions;
		updateModalPosition(event);
	}

</script>

<div class="box svelte-ohpquu">
	<LeadingIcon
		class="material-icons"
		style="margin-left: -4px; cursor:pointer"
		draggable={isDraggable}
		on:dragstart={(ev) => {
			const transferData = JSON.stringify({
            example,
            passFailInfo, // Include pass/fail dictionary
			});
			ev.dataTransfer.setData("text/plain", transferData);
			ev.dataTransfer.dropEffect = "copy";
		}}>
		<svg
			xmlns="http://www.w3.org/2000/svg"
			width="1em"
			height="1em"
			viewBox="0 0 24 24"
			><path
				fill="currentColor"
				d="M13 11h5l-1.5-1.5l1.42-1.42L21.84 12l-3.92 3.92l-1.42-1.42L18 13h-5v5l1.5-1.5l1.42 1.42L12 21.84l-3.92-3.92L9.5 16.5L11 18v-5H6l1.5 1.5l-1.42 1.42L2.16 12l3.92-3.92L7.5 9.5L6 11h5V6L9.5 7.5L8.08 6.08L12 2.16l3.92 3.92L14.5 7.5L13 6z" /></svg>
	</LeadingIcon>
	<span class="label svelte-ohpquu">input:</span>
	<span class="value svelte-ohpquu">
		{item[columnHash($settings.dataColumn)]}
	</span>
	<TrailingIcon
		class="material-icons"
		style="margin-bottom: 5px; margin-left: 0px; cursor: pointer; opacity: 0.8;"
		on:click={() => {
			runPrompt($model, $currentPromptId, {
				ids: [item[columnHash($settings.idColumn)]],
			});
		}}>
		play_circle
	</TrailingIcon>
	{#if modelColumn !== "" && item[modelColumn] !== null}
		<br />
		<span class="label svelte-ohpquu">output:</span>

			<div style="display: flex; justify-content: space-between; gap: 1rem; align-items: baseline;">
				{#if modelColumn_compare && item != item_compare}
				  <span class="value svelte-ohpquu">
					{item[modelColumn]}
				  </span>
				  <span class="value svelte-ohpquu">
					{item_compare[modelColumn_compare]}
				  </span>
				{:else}
				  <span class="value svelte-ohpquu">
					{item[modelColumn]}
				  </span>
				{/if}
			  </div>
		<span style="position:relative">
			<TrailingIcon
				class="material-icons thumb-up-icon"
				style="margin-bottom: 5px; margin-left: 0px; cursor: pointer; color: #97ca00;"
				title="Add positive examples to existing requirements"
				on:click={handleThumbUpClick}>
				thumb_up
			</TrailingIcon>
			<TrailingIcon
				class="material-icons thumb-down-icon"
				style="margin-bottom: 5px; margin-left: 3px; cursor: pointer; color: #e05d44;"
				title="Add negative examples to existing requirements"
				on:click={handleThumbDownClick}>
				thumb_down
			</TrailingIcon>
			{#if showOptions}
				<div
					class="modal"
					style="position: fixed; top: {menuY}px; left: {menuX}px; z-index: 10;"
					use:clickOutside
					on:click_outside={() => (showOptions = false)}>
					<div class="modal-content">
						<h3>Add a New Requirement if You Notice Something Missing</h3>
						<textarea
							bind:value={newRequirementInput}
							placeholder="Type a description for the new requirement..." />
						<div class="modal-actions">
							<button on:click={() => add_requirement()}
								>Add Requirement</button>
							<!-- <button on:click={closeModal}>Close</button> -->
						</div>
						<h3>OR Add Example To Related Requirements</h3>
						<div class="requirement-list">
							{#each Object.entries($requirements) as [id, req]}
								<UpdateRequirementCell
									requirement={req}
									exampleId={item[columnHash($settings.idColumn)]}
									feedbackPositive={feedbackThumbUp} />
							{/each}
						</div>
					</div>
				</div>
			{/if}
		</span>
	{/if}
	{#if Object.keys(evalColumns).length > 0}
		<br />
		{#each requirementIds as reqId}
			{#if evalColumns[reqId] !== "" && item[evalColumns[reqId]] !== null && item[evalColumns[reqId]] !== undefined}
				{#if modelColumn_compare && item != item_compare && item_compare[evalColumns_compare[reqId]] !== undefined && (item[evalColumns[reqId]] != item_compare[evalColumns_compare[reqId]])}
					<RequirementEvalChip
					id={reqId}
					isPass={item[evalColumns[reqId]] === true}
					rationale={item[rationaleColumns[reqId]]}
					item={item}
					evalColumns={evalColumns}
					reqId={reqId} 
					versionCompare={true}/>
				{:else}
					<RequirementEvalChip
					id={reqId}
					isPass={item[evalColumns[reqId]] === true}
					rationale={item[rationaleColumns[reqId]]}
					item={item}
					evalColumns={evalColumns}
					reqId={reqId} 
					versionCompare={false}/>
				{/if}
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
		line-height: 1.5; 
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
