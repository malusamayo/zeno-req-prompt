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

	export let id;
	export let isPass;
	export let rationale;

	let name;
	let menuX = 0;
	let menuY = 0;

	let requirement: Requirement;
	let hovering = false;

	$: {
		id;
		requirement = $requirements[id];
		name = requirement.name;
	}

	$: srcLink = `https://img.shields.io/badge/${name.replaceAll("-", "--")}-${
		isPass ? "pass" : "fail"
	}-${isPass ? "green" : "red"}`;

	function handleMouseOver(event) {
		const spanRect = event.target.getBoundingClientRect();
		menuX = spanRect.left;
		menuY = spanRect.bottom;
		hovering = true;
	}
</script>

<div style="position:relative; display:inline;">
	<img
		class="tag"
		draggable="false"
		src={srcLink}
		alt=""
		data={name}
		on:mouseover={handleMouseOver}
		on:focus={handleMouseOver}
		on:mouseleave={() => (hovering = false)}
		on:blur={() => (hovering = false)}
		on:keydown={() => {}} />
	{#if hovering}
		<div
			id="options-container"
			style="position:fixed; top: {menuY}px; left: {menuX}px;">
			<Paper style="padding: 3px 7px;" elevation={7}>
				<!-- <Content> -->
				<span class="rationale">
					<b>Rationale:</b>
					{rationale}
				</span>
				<!-- </Content> -->
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
