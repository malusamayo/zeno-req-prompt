<script lang="ts">
	import { mdiUpdate } from "@mdi/js";
	import IconButton, { Icon } from "@smui/icon-button";
	import { Svg } from "@smui/common";
	import { tooltip } from "@svelte-plugins/tooltips";
	import { prompts, currentPromptId, status, promptUpdating } from "../stores";
	import { ZenoService } from "../zenoservice";
	import CircularProgress from "@smui/circular-progress";

	const parser = new DOMParser();
	let prompt: string = $prompts.get($currentPromptId).text;
	let allowUpdates = false;
	let content = [];
	let contentEditableDiv;

	$: {
		$currentPromptId;
		switchPrompt();
	}

	$: {
		prompt;
		updateContent();
	}

	function switchPrompt() {
		prompt = $prompts.get($currentPromptId).text;
	}

	function updatePrompt() {
		promptUpdating.set(true);
		let newInnerPrompt = content
			.filter((x) => x.type === "text")
			.map((x) => x.value)
			.reduce((acc, val) => acc + val, "");
		ZenoService.createNewPrompt({
			text: newInnerPrompt,
			version: "",
			requirements: [],
		}).then((createdPrompts) => {
			// ZenoService.getCurrentPromptId().then((res) => {
			ZenoService.getCompleteColumns().then((cols) => {
				status.update((s) => {
					s.completeColumns = cols;
					return s;
				});
				currentPromptId.set(createdPrompts[0].version);
				prompts.update((pts) => {
					return pts.set(createdPrompts[0].version, createdPrompts[0]);
				});
				promptUpdating.set(false);
				allowUpdates = false;
			});
			// });
		});
	}

	function updateContent() {
		let parsedPrompt = parser.parseFromString(prompt, "text/xml");

		content = Array.from(parsedPrompt.children[0].children)
			.map((x) => [
				{ type: "tag", value: x.getAttribute("name") },
				{ type: "text", value: x.textContent },
			])
			.reduce((acc, val) => acc.concat(val), []);
	}

	function handleInput() {
		content = Array.from(contentEditableDiv.children).map(
			(node: HTMLElement) => {
				if (node.nodeType === Node.ELEMENT_NODE) {
					if (node.hasAttribute("data")) {
						return { type: "tag", value: node.getAttribute("data") };
					} else {
						return { type: "text", value: node.textContent };
					}
				}
			}
		);
		allowUpdates = true;
		console.log(content); // Updated content
	}

	// [TODO] allow users to write requirements explicitly
	// [TODO] prevent from deleting requirement tags
	function handleKeydown(e) {
		const selection = window.getSelection();
		const selectedNode = selection.anchorNode;

		// Check if an image is selected or in focus when Backspace or Delete is pressed
		if (
			(e.key === "Backspace" || e.key === "Delete") &&
			selectedNode &&
			selectedNode.nodeName === "DIV"
		) {
			e.preventDefault(); // Prevent the action
		}
		// if (e.key === "k" && e.metaKey) {
		// 	content = content.concat([{ type: "tag", value: "new-requirement" }]);
		// }
	}
</script>

<div class="inline">
	<div class="inline">
		<h4>Prompt</h4>
		{#if $promptUpdating}
			<CircularProgress
				style="height: 15px; width: 15px; margin-left: 10px;"
				indeterminate />
		{/if}
	</div>
	<div class="inline">
		<div
			use:tooltip={{
				content: "Update prompts",
				position: "left",
				theme: "zeno-tooltip",
			}}>
			<IconButton
				on:click={() => {
					if (allowUpdates) {
						updatePrompt();
					}
				}}
				style={allowUpdates ? "cursor:pointer" : "cursor:default"}>
				<Icon component={Svg} viewBox="0 0 24 24">
					{#if allowUpdates}
						<path fill="var(--G1)" d={mdiUpdate} />
					{:else}
						<path fill="var(--G4)" d={mdiUpdate} />
					{/if}
				</Icon>
			</IconButton>
		</div>
	</div>
</div>
<div
	contenteditable="true"
	bind:this={contentEditableDiv}
	class="promptbox"
	on:input={handleInput}
	on:keydown={handleKeydown}>
	{#each content as item}
		{@const srcLink = `https://img.shields.io/badge/${item.value.replace(
			"-",
			"--"
		)}-8A2BE2`}
		{#if item.type === "text"}
			<span>{item.value}</span>
		{:else if item.type === "tag"}
			<img src={srcLink} alt="" data={item.value} />
		{/if}
	{/each}
</div>

<style>
	img {
		pointer-events: none;
		margin-right: 2px;
	}
	.inline {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}
	.tag {
		display: inline-block;
		padding: 2px 5px;
		margin: 0 2px;
		background-color: #e0e0e0;
		border-radius: 4px;
		cursor: pointer;
	}

	.promptbox {
		outline: 1px solid #767676;
		min-height: 150px;
		padding: 5px;
		margin-bottom: 10px;
	}
</style>
