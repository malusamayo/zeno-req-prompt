<script lang="ts">
	import { columnHash } from "../util/util";
	import {
		currentPromptId,
		model,
		requirements,
		requirementUpdating,
		settings,
		status,
		suggestedRequirements,
	} from "../stores";
	import { ZenoColumnType, ZenoService } from "../zenoservice";
	import { clickOutside } from "../util/clickOutside";
	import RequirementEvalChip from "../metadata/chips/RequirementEvalChip.svelte";
	import { TrailingIcon } from "@smui/chips";
	import Paper, { Content } from "@smui/paper";
	import { Icon } from "@smui/button";
	import { InitialFocus } from "@smui/dialog";

	export let item;
	let modelColumn;
	let evalColumns;
	let rationaleColumns;

	let requirementIds;

	let showFeedback = false;
	let feedbackThumbUp;
	let feedbackText = "";

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

	function feedbackToRequirements() {
		requirementUpdating.set(true);
		ZenoService.suggestRequirementUpdates({
			model: $model,
			promptId: $currentPromptId,
			exampleId: item[columnHash($settings.idColumn)],
			isPositive: feedbackThumbUp,
			feedback: feedbackText,
		}).then((newRequirements) => {
			suggestedRequirements.set(newRequirements);
			showFeedback = false;
			feedbackText = "";
			requirementUpdating.set(false);
		});
	}

	function submit(e) {
		if (e.metaKey && e.key === "Enter") {
			e.preventDefault();
			feedbackToRequirements();
		}
	}
</script>

<div class="box svelte-ohpquu">
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
					showFeedback = !showFeedback;
					feedbackThumbUp = true;
				}}>
				thumb_up
			</TrailingIcon>
			<TrailingIcon
				class="material-icons"
				style="margin-bottom: 5px; margin-left: 3px; cursor: pointer; color: #e05d44;"
				on:click={() => {
					showFeedback = !showFeedback;
					feedbackThumbUp = false;
				}}>
				thumb_down
			</TrailingIcon>
			{#if showFeedback}
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
					rationale={item[rationaleColumns[reqId]]} />
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
</style>
