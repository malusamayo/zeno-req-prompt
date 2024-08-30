<script lang="ts">
	import { mdiUpdate } from "@mdi/js";
	import IconButton, { Icon } from "@smui/icon-button";
	import { Svg } from "@smui/common";
	import { tooltip } from "@svelte-plugins/tooltips";
	import { prompts, currentPromptId, status, promptUpdating } from "../stores";
	import { ZenoService } from "../zenoservice";
	import CircularProgress from "@smui/circular-progress";
	import RequirementChip from "./chips/RequirementChip.svelte";

	const parser = new DOMParser();
	let prompt: string = $prompts.get($currentPromptId).text;
	let allowUpdates = false;
	let contentEditableDiv: HTMLDivElement;

	$: {
		$currentPromptId;
		switchPrompt();
	}

	$: {
		prompt;
		if (contentEditableDiv) {
			updateContent();
		}
	}

	function switchPrompt() {
		prompt = $prompts.get($currentPromptId).text;
	}

	function updatePrompt() {
		promptUpdating.set(true);
		let newInnerPrompt = Array.from(contentEditableDiv.childNodes)
			.map((node: HTMLElement) => {
				if (node.nodeType === Node.ELEMENT_NODE) {
					if (node.hasAttribute("data")) {
						return "";
					} else {
						return node.textContent;
					}
				} else if (node.nodeType === Node.TEXT_NODE) {
					return node.textContent;
				}
			})
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
		if (contentEditableDiv) {
			contentEditableDiv.innerHTML = "";
		}
		let parsedPrompt = parser.parseFromString(prompt, "text/xml");

		let content = Array.from(parsedPrompt.children[0].children)
			.map((x) => {
				let arr = [];
				if (x.hasAttribute("name"))
					arr.push({ type: "tag", value: x.getAttribute("name") });
				arr.push({ type: "text", value: x.textContent });
				return arr;
			})
			.reduce((acc, val) => acc.concat(val), []);

		content.forEach((item) => {
			if (item.type === "text") {
				const textNode = document.createTextNode(item.value);
				contentEditableDiv.appendChild(textNode);
			} else if (item.type === "tag") {
				const imgNode = document.createElement("span");
				const reqChip = new RequirementChip({
					target: imgNode,
					props: {
						name: item.value,
					},
				});
				contentEditableDiv.appendChild(imgNode);
			}
		});
	}

	function handleInput() {
		allowUpdates = true;
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
			selectedNode.nodeName === "SPAN"
		) {
			e.preventDefault(); // Prevent the action
		}
		// if (e.key === "k" && e.metaKey) {
		// 	content = content.concat([{ type: "tag", value: "new-requirement" }]);
		// }
	}

	function handlePaste(event) {
		event.preventDefault();
		const clipboardData = event.clipboardData.getData("text");
		document.execCommand("insertHTML", false, clipboardData);
	}

	// $: {
	// 	console.log(content);
	// 	console.log(contentEditableDiv);
	// }
	// $: {
	// 	console.log(contentEditableDiv, "hey!!!");
	// }
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
	on:keydown={handleKeydown}
	on:paste={handlePaste} />

<style>
	.inline {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}
	.promptbox {
		outline: 1px solid #767676;
		min-height: 150px;
		padding: 5px;
		margin-bottom: 10px;
	}
</style>
