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
		showNewRequirement,
		requirementToEdit,
		requirements,
		promptToUpdate,
		suggestedRequirements,
	} from "../stores";
	import { ZenoService, type Requirement } from "../zenoservice";
	import { areRequirementsEqual } from "../zenoservice/models/prompt";
	import RequirementCell from "./cells/RequirementCell.svelte";
	import { TrailingIcon } from "@smui/chips";

	let newRequirementInput = "";
	// let displayedRequirements: { [key: string]: Requirement };

	$: inputChanged = newRequirementInput !== "";

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
			}
		);
	}

	function compile_to_prompt() {
		promptUpdating.set(true);
		suggestedRequirements.set({});
		ZenoService.createNewPrompt({
			text: "",
			version: "",
			requirements: $requirements,
		}).then((createdPrompts) => {
			prompts.update((pts) => {
				return pts.set(createdPrompts[0].version, createdPrompts[0]);
			});
			currentPromptId.set(createdPrompts[0].version);
			promptUpdating.set(false);
			promptToUpdate.set(false);
		});
	}

	function suggest_requirements() {
		suggestedRequirements.set({});
		requirementUpdating.set(true);
		ZenoService.suggestRequirements().then(($suggestedRequirements) => {
			suggestedRequirements.set($suggestedRequirements);
			requirementUpdating.set(false);
		});
	}

	function submit(e) {
		if (e.metaKey && e.key === "Enter") {
			e.preventDefault();
			add_requirement();
		}
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
					suggest_requirements();
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

{#each Object.entries($requirements) as [id, req]}
	<RequirementCell
		requirement={req}
		compare={$tab === "comparison"}
		suggested={false} />
{/each}
{#each Object.entries($suggestedRequirements) as [id, req]}
	<RequirementCell
		requirement={req}
		compare={$tab === "comparison"}
		suggested={true} />
{/each}

<div class="inline">
	<input
		placeholder="Write a new requirement here. ⌘ + Enter to submit."
		bind:value={newRequirementInput}
		on:keydown={submit} />
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
