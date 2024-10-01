<script lang="ts">
	import { Icon } from "@smui/icon-button";
	import Paper, { Content } from "@smui/paper";
	import { clickOutside } from "../../util/clickOutside";
	import type { Requirement } from "src/zenoservice";
	import {
		currentPromptId,
		prompts,
		requirements,
		requirementToEdit,
		showNewFolder,
		showNewRequirement,
		showNewSlice,
		showSliceFinder,
	} from "../../stores";

	// export let requirement: Requirement;
	export let name; // = requirement.name;
	export let id;
	let requirement: Requirement;
	let showOptions = false;
	let menuX = 0;
	let menuY = 0;

	$: {
		name;
		requirement = $requirements[id];
	}
	$: srcLink = `https://img.shields.io/badge/${name.replaceAll(
		"-",
		"--"
	)}-a463f2`;

	function handleSpanClick(event) {
		// const spanRect = event.target.getBoundingClientRect();
		// menuX = spanRect.left;
		// menuY = spanRect.bottom;
		// showOptions = !showOptions;
		if (requirement == null) {
			return;
		}

		showNewSlice.set(false);
		showNewFolder.set(false);
		showSliceFinder.set(false);
		showNewRequirement.update((d) => !d);
		requirementToEdit.set(requirement);
	}
</script>

<span>
	<img
		class="tag"
		draggable="false"
		src={srcLink}
		alt=""
		data={name}
		on:click={handleSpanClick}
		on:keydown={() => {}} />
	<!-- {#if showOptions}
		<div
			id="options-container"
			style="position:fixed; top: {menuY}px; left: {menuX}px; 
		z-index: 5; width: 70px"
			use:clickOutside
			on:click_outside={() => (showOptions = false)}>
			<Paper style="padding: 3px 0px;" elevation={7}>
				<Content>
					<div
						class="option"
						on:keydown={() => ({})}
						on:click={(e) => {
							e.stopPropagation();
							showOptions = false;
						}}>
						<Icon style="font-size: 12px;" class="material-icons">edit</Icon
						>&nbsp;
						<span>Re-write</span>
					</div>
					<div
						class="option"
						on:keydown={() => ({})}
						on:click={(e) => {
							e.stopPropagation();
							showOptions = false;
						}}>
						<Icon style="font-size: 12px;" class="material-icons"
							>bug_report</Icon
						>&nbsp;
						<span>Tests</span>
					</div>
				</Content>
			</Paper>
		</div>
	{/if} -->
</span>

<style>
	.tag {
		cursor: pointer;
		/* pointer-events: none; */
		margin-right: 2px;
		margin-bottom: -2.5px;
	}
	#options-container {
		/* left: 40px; */
		z-index: 5;
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
