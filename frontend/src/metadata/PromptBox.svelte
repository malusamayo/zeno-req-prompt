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
		// placeholder to prevent crashing when insertBefore 0 index
		// content = [{ type: "", value: " " }].concat(content);

		console.log(content);
	}

	function removeEmptyNodes(parentNode) {
		parentNode.childNodes.forEach((node) => {
			if (node.nodeType === Node.TEXT_NODE && node.textContent === "") {
				parentNode.removeChild(node);
			}
		});
	}

	function handleInput(event) {
		removeEmptyNodes(event.target);
		const textNodes = Array.from(event.target.childNodes);
		const updatedContent = textNodes
			.map((node: HTMLElement) => {
				if (node.nodeType === Node.TEXT_NODE) {
					return { type: "text", value: node.textContent };
				} else if (
					node.nodeType === Node.ELEMENT_NODE &&
					node.dataset.type === "tag"
				) {
					return { type: "tag", value: node.innerText };
				}
			})
			.filter(Boolean);

		content = updatedContent;
		allowUpdates = true;
		console.log(content); // Updated content
	}

	// [TODO] allow users to write requirements explicitly
	function handleKeydown(e) {
		if (e.key === "k" && e.metaKey) {
			// content = content.concat([{ type: "tag", value: "" }]);
		}
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
	class="promptbox"
	on:input={handleInput}
	on:keydown={handleKeydown}>
	{#each content as item}
		{#if item.type === "text"}
			{item.value}
		{:else if item.type === "tag"}
			<span class="tag" data-type="tag" contenteditable="false"
				>{item.value}</span>
		{/if}
	{/each}
</div>

<style>
	textarea {
		min-width: 330px;
		min-height: 100px;
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
		min-height: 100px;
		padding: 5px;
	}
</style>
