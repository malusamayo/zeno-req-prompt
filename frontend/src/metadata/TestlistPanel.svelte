<script lang="ts">
	import { mdiArrowDownBold, mdiRefresh, mdiPlus } from "@mdi/js";
	import Button from "@smui/button";
	import CircularProgress from "@smui/circular-progress";
	import { Svg } from "@smui/common";
	import IconButton, { Icon } from "@smui/icon-button";
	import { tooltip } from "@svelte-plugins/tooltips";
	import {
		status,
		selectionPredicates,
		selections,
		showNewFolder,
		showNewSlice,
		showNewTag,
		showSliceFinder,
		tab,
		promptUpdating,
		requirementUpdating,
		prompts,
		currentPromptId,
		model,
		showNewRequirement,
		requirementToEdit,
		requirements,
		promptToUpdate,
		suggestedRequirements,
		showNewGoal,
		goals,
	} from "../stores";
	import { ZenoService, type Requirement } from "../zenoservice";
	import TestCell from "./cells/TestCell.svelte";
	import { TrailingIcon } from "@smui/chips";
	import type { RequirementTree } from "../zenoservice";

	let newRequirementInput = "";
	let newGoalInput = "";
	let tempGoal = "";
	// let displayedRequirements: { [key: string]: Requirement };

	$: inputChanged = newRequirementInput !== "";

	$: {
		$model;
		$currentPromptId;
	}

	// $: {
	// 	$requirements;
	// 	displayedRequirements = JSON.parse(JSON.stringify($requirements));
	// 	Object.entries(displayedRequirements).forEach(([req_id, req]) => {
	// 		req.mode = "";
	// 	});
	// }

	// $: {
	// 	$suggestedRequirements;
	// 	displayedRequirements = JSON.parse(JSON.stringify($requirements));
	// 	Object.entries(displayedRequirements).forEach(([req_id, req]) => {
	// 		req.mode = "";
	// 	});
	// 	if (Object.keys($suggestedRequirements).length > 0) {
	// 		Object.entries($suggestedRequirements).forEach(([req_id, req]) => {
	// 		if (!(req_id in displayedRequirements)) {
	// 		displayedRequirements[req_id] = { ...req, mode: "new" };
	// 		} else if (
	// 		!areRequirementsEqual(
	// 		$suggestedRequirements[req_id],
	// 		displayedRequirements[req_id]
	// 		)
	// 		) {
	// 		displayedRequirements[req_id] = { ...req, mode: "edited" };
	// 		}
	// 		});
	// 		Object.entries($requirements).forEach(([req_id, req]) => {
	// 		if (!(req_id in $suggestedRequirements)) {
	// 		displayedRequirements[req_id] = { ...req, mode: "deleted" };
	// 		}
	// 		});
	// 	}
	// }

	function get_max_requirement_id() {
		return Math.max(
			Math.max(...Object.keys($requirements).map((id) => Number(id))),
			0
		);
	}

	function add_requirement() {
		let requirement: Requirement = {
			id: (get_max_requirement_id() + 1).toString(),
			name: "",
			description: newRequirementInput,
			promptSnippet: "",
			evaluationMethod: ""
		};

		requirements.update(($reqs) => {
			$reqs[requirement.id] = requirement;
			return $reqs;
		});

        ZenoService.saveTests($requirements);

	}

</script>

<div id="requirement-header" class="inline">
	<div class="inline">
		<h4>Testcases</h4>
		{#if $requirementUpdating}
			<CircularProgress
				style="height: 15px; width: 15px; margin-left: 10px;"
				indeterminate />
		{/if}
	</div>

</div>

{#each Object.entries($requirements) as [id, req]}
	<TestCell
		requirement={req}
		compare={$tab === "comparison"}
		suggested={false} />
{/each}

<div class="inline">
	<input
		placeholder="Write a new testcase here. Enter to submit."
		bind:value={newRequirementInput}
		on:drop={(ev) => {
			ev.preventDefault();
		}}
		on:keydown={(e) => {
			if (e.key === "Enter") {
				e.preventDefault();
				add_requirement();
				newRequirementInput = "";
			}
		}} />
	<span>
		<IconButton
			on:click={() => {
				if (inputChanged) {
					add_requirement();
				}
			}}
			style={inputChanged ? "cursor:pointer" : "cursor:default"}>
			<Icon component={Svg} viewBox="0 0 24 24">
				{#if inputChanged}
					<path fill="var(--G1)" d={mdiPlus} />
				{:else}
					<path fill="var(--G4)" d={mdiPlus} />
				{/if}
			</Icon>
		</IconButton>
	</span>
</div>

<style>
	#requirement-header {
		position: sticky;
		top: -10px;
		z-index: 3;
		background-color: var(--Y2);
	}
	.inline {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}
	input {
		position: relative;
		overflow: visible;
		border: 0.5px solid var(--G4);
		border-radius: 4px;
		margin-top: 5px;
		display: flex;
		padding-left: 10px;
		padding-right: 10px;
		min-height: 36px;
		width: 85%;
		font-size: small;
		font-weight: lighter;
	}
</style>