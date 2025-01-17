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
	import RequirementCell from "./cells/RequirementCell.svelte";
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

	function add_requirement(feature) {
		let requirement: Requirement = {
			id: (get_max_requirement_id() + 1).toString(),
			name: "",
			description: newRequirementInput,
			promptSnippet: "",
			evaluationMethod: "",
			feature: feature,
		};

		requirements.update(($reqs) => {
			$reqs[requirement.id] = requirement;
			return $reqs;
		});

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
			goals.update(($goals) => {
				if (!$goals.includes(feature)) {
					$goals.push(feature);
				}
				return $goals;
			});
			promptToUpdate.set(true);
			newRequirementInput = "";
			requirementUpdating.set(false);
		});
	}

	function compile_to_prompt() {
		promptUpdating.set(true);
		suggestedRequirements.set({});
		ZenoService.createNewPrompt({
			text: "",
			version: "",
			requirements: $requirements,
			task: $prompts.get($currentPromptId).task,
		}).then((createdPrompts) => {
			prompts.update((pts) => {
				return pts.set(createdPrompts[0].version, createdPrompts[0]);
			});
			currentPromptId.set(createdPrompts[0].version);
			promptUpdating.set(false);
			promptToUpdate.set(false);
		});
	}

	function suggest_requirements(prompt_id, model) {
		status.update((s) => {
			s.status = "Brainstorming requirements";
			return s;
		});
		suggestedRequirements.set({});
		requirementUpdating.set(true);
		ZenoService.suggestRequirements({
			promptId: prompt_id,
			model: model,
		}).then(($suggestedRequirements) => {
			suggestedRequirements.set($suggestedRequirements);
			requirementUpdating.set(false);
			status.update((s) => {
				s.status = "Done processing";
				return s;
			});
		});
	}

	function organizeRequirements(
		requirements: {
			[key: string]: Requirement;
		},
		suggestRequirements: {
			[key: string]: Requirement;
		}
	): {
		[key: string]: RequirementTree;
	} {
		const tree: Record<string, RequirementTree> = {};

		function add_requirement(requirement, suggested) {
			if (!requirement.feature) {
				requirement.feature = "uncategorized";
			}
			const feature = requirement.feature;

			if (!tree[feature]) {
				tree[feature] = {
					feature,
					requirements: [],
					showNewRequirement: false,
				};
			}

			tree[feature].requirements.push({
				requirement,
				suggested,
			});
		}

		Object.values(requirements).forEach((requirement) => {
			add_requirement(requirement, false);
		});

		Object.values(suggestRequirements).forEach((requirement) => {
			add_requirement(requirement, true);
		});

		return tree;
	}

	// Adjust `getCategoryColor` to handle priority-based color adjustment
	function getCategoryColor(
		category: string | undefined,
		priority: string | undefined
	): string {
		let baseColor;

		if (category === "content") {
			baseColor = priority === "soft" ? "#FFEFE2" : "#FFDDC1"; // Lighter and regular colors for content
		} else if (category === "structure") {
			baseColor = priority === "soft" ? "#E3F2E9" : "#D1E7DD"; // Lighter and regular colors for structure
		} else if (category === "presentation") {
			baseColor = priority === "soft" ? "#E8F0FF" : "#CFE2FF"; // Lighter and regular colors for presentation
		} else {
			baseColor = "white"; // Default white
		}

		return baseColor;
	}

	function createNewGoal(feature) {
		let requirement: Requirement = {
			id: (get_max_requirement_id() + 1).toString(),
			name: "",
			description: "Write new requirements here...",
			promptSnippet: "",
			evaluationMethod: "",
			feature: feature,
		};
		requirements.update(($reqs) => {
			$reqs[requirement.id] = requirement;
			return $reqs;
		});
	}

	$: requirementTree = organizeRequirements(
		$requirements,
		$suggestedRequirements
	);
	let previousGoal = "";

	function startEditingGoal(goal) {
		previousGoal = goal;
	}

	function updateGoal(prevGoal, newGoal) {
		const oldGoal = prevGoal;
		if (newGoal == prevGoal) {
			return;
		}
		if (requirementTree[newGoal]) {
			requirementTree[newGoal].requirements = requirementTree[
				newGoal
			].requirements.concat(requirementTree[oldGoal].requirements);
			delete requirementTree[oldGoal];
			return;
		}
		requirementTree[newGoal] = requirementTree[oldGoal];
		requirementTree[newGoal].requirements.forEach((reqObj) => {
			reqObj.requirement.feature = newGoal;
			requirements.update(($reqs) => {
				$reqs[reqObj.requirement.id].feature = newGoal;
				return $reqs;
			});
		});
		delete requirementTree[oldGoal];
	}

	function deleteGoal(goal) {
		if (requirementTree[goal] !== undefined) {
			if (!$goals.includes("uncategorized")) {
				$goals.push("uncategorized");
				requirementTree["uncategorized"] = requirementTree[goal];
			} else {
				requirementTree["uncategorized"].requirements = requirementTree[
					"uncategorized"
				].requirements.concat(requirementTree[goal].requirements);
			}
			requirementTree[goal].requirements.forEach((reqObj) => {
				reqObj.requirement.feature = "uncategorized";
				requirements.update(($reqs) => {
					$reqs[reqObj.requirement.id].feature = "uncategorized";
					return $reqs;
				});
			});
			delete requirementTree[goal];
		}
		goals.update(($goals) => $goals.filter((g) => g !== goal));
	}

	// $: {
	// 	$promptToUpdate;
	// 	if ($promptToUpdate) {
	// 		compile_to_prompt();
	// 		promptToUpdate.set(false);
	// 	}
	// }
</script>

<div id="requirement-header" class="inline">
	<div class="inline">
		<h4>Requirements</h4>
		{#if $requirementUpdating}
			<CircularProgress
				style="height: 15px; width: 15px; margin-left: 10px;"
				indeterminate />
		{/if}
	</div>

	<div class="inline">
		<div
			use:tooltip={{
				content: "Brainstorm requirements.",
				position: "left",
				theme: "zeno-tooltip",
			}}>
			<IconButton
				on:click={() => {
					suggest_requirements($currentPromptId, $model);
				}}
				style="cursor:pointer; margin-top:-5px">
				<Icon class="material-icons" style="color: #efb118">lightbulb_2</Icon>
			</IconButton>
		</div>
		<div
			use:tooltip={{
				content: "Create a new goal.",
				position: "left",
				theme: "zeno-tooltip",
			}}>
			<IconButton
				on:click={(e) => {
					e.stopPropagation();
					showNewSlice.set(false);
					showNewFolder.set(false);
					showSliceFinder.set(false);
					showSliceFinder.set(false);
					showNewGoal.update((d) => !d);
				}}
				style="cursor:pointer; margin-top:-5px">
				<Icon class="material-icons" style="color: lightgrey">add_circle</Icon>
			</IconButton>
		</div>
		<!-- <div

use:tooltip={{

content: "Compile to prompt.",

position: "left",

theme: "zeno-tooltip",

}}>

<IconButton

on:click={() => {

compile_to_prompt();

}}

style="cursor:pointer">

<Icon component={Svg} viewBox="0 0 24 24">

{#if $promptToUpdate}

<path fill="var(--G1)" d={mdiArrowDownBold} />

{:else}

<path fill="var(--G4)" d={mdiArrowDownBold} />

{/if}

</Icon>

</IconButton>
        </div> -->
	</div>
</div>

<!-- {#each Object.entries($requirements) as [id, req]}

<RequirementCell

requirement={req}

compare={$tab === "comparison"}

suggested={false} />
{/each} -->

<!-- <div class="requirement-tree">
    {#each requirementTree as featureGroup}
        <div class="feature-node">
            <h3 class="feature-title">{featureGroup.feature}</h3>
            {#each featureGroup.requirements as { requirement, color, shade }}
                <div class="requirement-node" style="background-color: {color}; opacity: {shade === 'dark' ? 0.9 : shade === 'light' ? 0.6 : 0.8}">
                    <RequirementCell

requirement={requirement}

compare={$tab === "comparison"}

suggested={false} />
                </div>
            {/each}
        </div>
    {/each}
</div> -->

{#each $goals as goal}
	{@const featureGroup = requirementTree[goal]}
	<div
		class="feature-node"
		on:drop={(ev) => {
			ev.preventDefault();
			const data = ev.dataTransfer.getData("text/plain");
			const requirement = JSON.parse(data);
			if (requirement.feature === undefined) {
				return;
			}
			requirements.update(($reqs) => {
				let requirementToEdit = $reqs[Number(requirement.id)];
				requirementToEdit.feature = goal;
				return $reqs;
			});
		}}>
		<div class="goal-input-container">
			<div class="goal-title">
				{#if goal !== "uncategorized"}
					<div
						contenteditable="true"
						class="feature-title"
						on:focus={() => startEditingGoal(goal)}
						on:blur={() => updateGoal(previousGoal, goal)}
						on:keydown={(e) => {
							if (e.key === "Enter") {
								e.preventDefault();
								e.target.blur();
							}
						}}>
						{goal}
					</div>
					<button
						type="button"
						class="delete-icon"
						on:click={() => deleteGoal(goal)}>
						✕
					</button>
				{:else}
					<div class="feature-title">
						{goal}
					</div>
				{/if}
			</div>
		</div>

		<!-- <TrailingIcon

class="material-icons"

style="margin-bottom: 4px; color: lightgrey; cursor: pointer;"

on:click={() => {

featureGroup.showNewRequirement = !featureGroup.showNewRequirement;

}}>

add_circle
</TrailingIcon> -->

		{#if featureGroup}
			{#each featureGroup.requirements as { requirement, suggested }}
				<RequirementCell
					{requirement}
					compare={$tab === "comparison"}
					{suggested} />
			{/each}
		{/if}

		<!-- {#if featureGroup.showNewRequirement}{/if} -->
	</div>
{/each}
<!-- <div class="feature-node">

<input

class="new-feature-title"

placeholder="New goals..."

bind:value={newGoalInput}

on:keydown={(e) => {

if (e.key === "Enter") {

e.preventDefault();

createNewGoal(newGoalInput);

newGoalInput = "";

}

}} />
</div> -->

<!-- <RequirementCell

requirement={{

id: (get_max_requirement_id() + 1).toString(),

name: "",

description: "Write new requirements here...",

promptSnippet: "",

evaluationMethod: "",

feature: "uncategorized",

}}

compare={$tab === "comparison"}
suggested={false} /> -->

<!-- {#each Object.entries($suggestedRequirements) as [id, req]}

<RequirementCell

requirement={req}

compare={$tab === "comparison"}

suggested={true} />
{/each} -->

<div class="inline">
	<input
		placeholder="Write a new requirement here. Enter to submit."
		bind:value={newRequirementInput}
		on:drop={(ev) => {
			ev.preventDefault();
		}}
		on:keydown={(e) => {
			if (e.key === "Enter") {
				e.preventDefault();
				add_requirement("uncategorized");
				newRequirementInput = "";
			}
		}} />
	<!-- <span>

<IconButton

on:click={() => {

if (inputChanged) {

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
</span> -->
</div>

<style>
	#requirement-header {
		position: sticky;
		top: -10px;
		z-index: 3;
		background-color: var(--Y2);
		margin-bottom: -10px;
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
		margin-top: 8px;
		display: flex;
		padding-left: 10px;
		padding-right: 10px;
		min-height: 36px;
		width: 85%;
		font-size: small;
		font-weight: lighter;
	}

	.feature-node {
		display: flex;
		flex-direction: column;
	}

	.feature-title {
		font-weight: bold;
		font-size: 14px;
		border: none;
		background-color: transparent;
		color: var(--G1);
		outline: none;
		margin-top: 10px;
		padding-left: 5px;
		padding-right: 5px;
	}

	.feature-title:focus {
		background-color: #ffffff; /* Light grey background to indicate editing */
		border: 1px solid var(--G4);
		border-radius: 4px;
	}

	.feature-title-uncategorized {
		font-weight: bold;
		font-size: 14px;
		border: none;
		background-color: transparent;
		color: var(--G1);
		outline: none;
		margin-top: 18px;
		margin-left: 7px;
		margin-bottom: 7px;
	}

	.goal-input-container {
		display: flex;
		align-items: center;
	}
	.goal-title {
		display: flex;
		align-items: center;
	}

	.delete-icon {
		background: none;
		border: none;
		cursor: pointer;
		color: grey;
		font-size: 10px; /* Smaller size for the "X" */
		margin-left: -5px; /* Minimal space between title and "X" */
		margin-bottom: -5px;
	}
	.delete-icon:hover {
		color: darkgrey;
		/* Darker grey on hover */
	}

	/* input {

font-weight: bold;

margin-bottom: 10px;

font-size: 14px; 

border: 1px solid var(--G4);

border-radius: 4px;

padding: 3px;

color: var(--G1);
	} */
</style>
