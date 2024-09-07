<script lang="ts">
	import { mdiCogs, mdiMagicStaff, mdiPlus } from "@mdi/js";
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
		prompts,
		currentPromptId,
		showNewRequirement,
		requirementToEdit,
		requirements,
	} from "../stores";
	import { ZenoService } from "../zenoservice";
	import RequirementCell from "./cells/RequirementCell.svelte";

	let newRequirementInput = "";

	function get_max_requirement_id() {
		return Math.max(
			Math.max(...Object.keys($requirements).map((id) => Number(id))),
			0
		);
	}

	function compile_to_prompt() {
		promptUpdating.set(true);
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
		});
	}
</script>

<div id="requirement-header" class="inline">
	<div class="inline">
		<h4>Requirements</h4>
		{#if $promptUpdating}
			<CircularProgress
				style="height: 15px; width: 15px; margin-left: 10px;"
				indeterminate />
		{/if}
	</div>

	<div class="inline">
		<div
			use:tooltip={{
				content: "Compile requirements to prompt.",
				position: "left",
				theme: "zeno-tooltip",
			}}>
			<IconButton on:click={compile_to_prompt}>
				<Icon component={Svg} viewBox="0 0 24 24">
					{#if $selectionPredicates.predicates.length > 0}
						<path fill="#6a1a9a" d={mdiCogs} />
					{:else}
						<path fill="var(--G1)" d={mdiCogs} />
					{/if}
				</Icon>
			</IconButton>
		</div>
	</div>
</div>

{#each Object.entries($requirements) as [id, req]}
	<RequirementCell requirement={req} compare={$tab === "comparison"} />
{/each}

<div class="inline">
	<input
		placeholder="Write a new requirement here."
		bind:value={newRequirementInput} />
	<div>
		<IconButton
			on:click={() => {
				requirementToEdit.set({
					id: (get_max_requirement_id() + 1).toString(),
					name: "",
					description: newRequirementInput,
					promptSnippet: "",
					evaluationMethod: "",
				});
				showNewRequirement.update((d) => !d);
				showNewSlice.set(false);
				showNewFolder.set(false);
				showSliceFinder.set(false);
			}}>
			<Icon component={Svg} viewBox="0 0 24 24">
				<path fill="var(--G1)" d={mdiPlus} />
			</Icon>
		</IconButton>
	</div>
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
