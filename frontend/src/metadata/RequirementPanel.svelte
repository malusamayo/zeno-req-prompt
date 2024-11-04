<script lang="ts">
	import { mdiArrowDownBold, mdiRefresh, mdiPlus } from "@mdi/js";
	import Button from "@smui/button";
	import CircularProgress from "@smui/circular-progress";
	import { Svg } from "@smui/common";
	import IconButton, { Icon } from "@smui/icon-button";
	import { tooltip } from "@svelte-plugins/tooltips";
	import {
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
	} from "../stores";
	import { ZenoService, type Requirement } from "../zenoservice";
	import RequirementCell from "./cells/RequirementCell.svelte";
	import { TrailingIcon } from "@smui/chips";
	import type { RequirementTree } from "../zenoservice";

	let newRequirementInput = "";
	let newGoalInput = "";
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
	// 			if (!(req_id in displayedRequirements)) {
	// 				displayedRequirements[req_id] = { ...req, mode: "new" };
	// 			} else if (
	// 				!areRequirementsEqual(
	// 					$suggestedRequirements[req_id],
	// 					displayedRequirements[req_id]
	// 				)
	// 			) {
	// 				displayedRequirements[req_id] = { ...req, mode: "edited" };
	// 			}
	// 		});
	// 		Object.entries($requirements).forEach(([req_id, req]) => {
	// 			if (!(req_id in $suggestedRequirements)) {
	// 				displayedRequirements[req_id] = { ...req, mode: "deleted" };
	// 			}
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
		suggestedRequirements.set({});
		requirementUpdating.set(true);
		ZenoService.suggestRequirements({ promptId: prompt_id, model: model }).then(
			($suggestedRequirements) => {
				suggestedRequirements.set($suggestedRequirements);
				requirementUpdating.set(false);
			}
		);
	}

	function organizeRequirements(requirements: {
		[key: string]: Requirement;
	}): RequirementTree[] {
		const tree: Record<string, RequirementTree> = {};

		Object.values(requirements).forEach((requirement) => {
			const feature = requirement.feature || "General"; // Default feature if not specified
			const categoryColor = getCategoryColor(
				requirement.category,
				requirement.priority
			); // Adjust color based on priority

			if (!tree[feature]) {
				tree[feature] = {
					feature,
					requirements: [],
					showNewRequirement: false,
				};
			}

			tree[feature].requirements.push({
				requirement,
				color: categoryColor, // Only the color is passed, without shade
			});
		});

		return Object.values(tree);
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

	$: requirementTree = organizeRequirements($requirements);
	$: suggestedrequirementTree = organizeRequirements($suggestedRequirements);

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

{#each requirementTree as featureGroup}
	<div class="feature-node">
		<span class="feature-title">{featureGroup.feature}</span>
		<TrailingIcon
			class="material-icons"
			style="margin-bottom: 4px; color: lightgrey; cursor: pointer;"
			on:click={() => {
				featureGroup.showNewRequirement = !featureGroup.showNewRequirement;
			}}>
			add_circle
		</TrailingIcon>

		{#each featureGroup.requirements as { requirement, color }}
			<RequirementCell
				{requirement}
				{color}
				compare={$tab === "comparison"}
				suggested={false} />
		{/each}

		{#if featureGroup.showNewRequirement}
			<RequirementCell
				requirement={{
					id: (get_max_requirement_id() + 1).toString(),
					name: "",
					description: "Write new requirements here...",
					promptSnippet: "",
					evaluationMethod: "",
					feature: featureGroup.feature,
				}}
				color={"white"}
				compare={$tab === "comparison"}
				suggested={false}
				newRequirement={true} />
		{/if}
	</div>
{/each}
<div class="feature-node">
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
</div>

<!-- {#each Object.entries($suggestedRequirements) as [id, req]}
	<RequirementCell
		requirement={req}
		compare={$tab === "comparison"}
		suggested={true} />
{/each} -->

{#each suggestedrequirementTree as featureGroup}
	<div class="feature-node">
		<h3 class="feature-title">{featureGroup.feature}</h3>
		{#each featureGroup.requirements as { requirement, color }}
			<RequirementCell
				{requirement}
				{color}
				compare={$tab === "comparison"}
				suggested={true} />
		{/each}
	</div>
{/each}

<!-- <div class="inline">
	<input
		placeholder="Add a new goal here. ⌘ + Enter to submit."
		bind:value={newRequirementInput}
		on:keydown={(e) => {
			if (e.metaKey && e.key === "Enter") {
				e.preventDefault();
			}
		}} />
	<span>
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
	</span>
</div> -->

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
	/* input {
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
	} */

	.feature-node {
		margin-bottom: 20px;
	}

	.feature-title {
		font-weight: bold;
		margin-bottom: 10px;
		font-size: 14px; /* Set to any smaller size you prefer */
		color: var(--G1);
	}

	input {
		font-weight: bold;
		margin-bottom: 10px;
		font-size: 14px; /* Set to any smaller size you prefer */
		border: 1px solid var(--G4);
		border-radius: 4px;
		padding: 3px;
		color: var(--G1);
	}
</style>
