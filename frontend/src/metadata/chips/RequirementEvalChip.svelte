<script lang="ts">
	import { Icon } from "@smui/icon-button";
	import { columnHash } from "../../util/util";
	import Paper, { Content } from "@smui/paper";
	import { clickOutside } from "../../util/clickOutside";
	import type { Requirement } from "src/zenoservice";
	import { ZenoService } from "../../zenoservice";
	import { TrailingIcon, LeadingIcon } from "@smui/chips";
	import {
		currentPromptId,
		prompts,
		requirements,
		requirementToEdit,
		showNewFolder,
		showNewRequirement,
		showNewSlice,
		showSliceFinder,
		requirementUpdating,
		model,
		settings,
	} from "../../stores";
	// import { ZenoColumnType, ZenoService } from "src/zenoservice";

	export let id;
	export let isPass;
	export let rationale;
	export let item;
	export let evalColumns;
	export let reqId;

	let name;
	let menuX = 0;
	let menuY = 0;

	let requirement: Requirement;
	let hovering = false;

	$: {
		id;
		requirement = $requirements[id];
		name = requirement.name;
		$model;
	}

	$: srcLink = `https://img.shields.io/badge/${name.replaceAll("-", "--")}-${
		isPass ? "pass" : "fail"
	}-${isPass ? "green" : "red"}`;

	// function handleMouseOver(event) {
	// 	const spanRect = event.target.getBoundingClientRect();
	// 	menuX = spanRect.left;
	// 	menuY = spanRect.bottom;
	// 	hovering = !hovering;
	// }
	function handleMouseOver(event) {
		const spanRect = event.target.getBoundingClientRect();
		// Adjust for scroll position
		menuX = spanRect.left + window.scrollX;
		menuY = spanRect.bottom + window.scrollY;
		hovering = !hovering; // Toggles the visibility on click
	}

	function feedbackToEvaluators(eval_res, reqId) {
		requirementUpdating.set(true);
		ZenoService.evaluatorUpdates({
			model: $model,
			promptId: $currentPromptId,
			exampleId: String(item[columnHash($settings.idColumn)]),
			corrected_eval: !eval_res,
			requirementId: reqId,
		}).then((newRequirements) => {
			requirements.set(newRequirements);
			requirementUpdating.set(false);
		});
	}
</script>

<div
	style="position:relative; display:inline;"
	on:mouseenter={() => (hovering = true)}
	on:mouseleave={() => (hovering = false)}>
	<img
		class="tag"
		draggable="false"
		src={srcLink}
		alt=""
		data={name}
		on:mouseover={handleMouseOver}
		on:focus={handleMouseOver}
		on:keydown={() => {}} />

	{#if hovering}
		<div
			id="options-container"
			style="position:fixed; top: {menuY}px; left: {menuX}px;"
			on:mouseenter={() => (hovering = true)}
			on:mouseleave={() => (hovering = false)}>
			<Paper style="padding: 3px 7px;" elevation={7}>
				<span class="rationale">
					<b>Rationale:</b>
					{rationale}
					<TrailingIcon
						class="material-icons"
						style="margin-bottom: 10px; margin-left:0px; margin-right: 5px; cursor: pointer; color: #e05d44;"
						on:click={() => {
							feedbackToEvaluators(item[evalColumns[reqId]], reqId);
						}}>
						thumb_down
					</TrailingIcon>
				</span>
			</Paper>
		</div>
	{/if}
</div>

<style>
	.tag {
		cursor: pointer;
		/* pointer-events: none; */
		margin-right: 2px;
		margin-top: 10px;
	}
	.rationale {
		font-size: 12px;
	}
	#options-container {
		/* left: 40px; */
		z-index: 5;
		max-width: 300px;
	}
	.option {
		display: flex;
		flex-direction: row;
		align-items: center;
		cursor: pointer;
		max-width: 70px;
		padding: 0px 3px;
	}
	.option span {
		font-size: 12px;
	}
	.option:hover {
		background: var(--G5);
	}
</style>
