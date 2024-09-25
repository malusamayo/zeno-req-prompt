<script lang="ts">
	import { mdiArrowUpBold, mdiPlayOutline, mdiUpdate } from "@mdi/js";
	import IconButton, { Icon } from "@smui/icon-button";
	import { Svg } from "@smui/common";
	import { tooltip } from "@svelte-plugins/tooltips";
	import {
		prompts,
		model,
		currentPromptId,
		status,
		promptUpdating,
		requirements,
	} from "../stores";
	import { ZenoService } from "../zenoservice";
	import CircularProgress from "@smui/circular-progress";
	import RequirementChip from "./chips/RequirementChip.svelte";
	import RequirementSpan from "./chips/RequirementSpan.svelte";
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

	function getInnerText(el) {
		var sel,
			range,
			innerText = "";
		if (
			typeof document.getSelection != null &&
			typeof document.body.createTextRange != "undefined"
		) {
			range = document.body.createTextRange();
			range.moveToElementText(el);
			innerText = range.text;
		} else if (
			typeof window.getSelection != "undefined" &&
			typeof document.createRange != "undefined"
		) {
			sel = window.getSelection();
			sel.selectAllChildren(el);
			innerText = "" + sel;
			sel.removeAllRanges();
		}
		return innerText;
	}

	function updatePrompt() {
		promptUpdating.set(true);
		let newInnerPrompt = getInnerText(contentEditableDiv);
		ZenoService.createNewPrompt({
			text: newInnerPrompt,
			version: "",
			requirements: $requirements,
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
				requirements.set(createdPrompts[0].requirements);
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

		let promptWithNewlines = prompt.replace(/\n/g, "[NEWLINE]");
		let parsedPrompt = parser.parseFromString(promptWithNewlines, "text/xml");

		let content = Array.from(parsedPrompt.children[0].childNodes)
			.map((node: HTMLElement) => {
				let arr = [];
				if (node.nodeType === Node.ELEMENT_NODE) {
					if (node.hasAttribute("name")) {
						arr.push({
							type: "tag",
							value: node.getAttribute("name"),
							id: node.getAttribute("id"),
						});
						arr.push({
							type: "req-text",
							value: node.textContent,
							id: node.getAttribute("id"),
						});
					} else {
						arr.push({ type: "text", value: node.textContent });
					}
				} else if (node.nodeType === Node.TEXT_NODE) {
					arr.push({ type: "text", value: node.textContent });
				}
				return arr;
			})
			.reduce((acc, val) => acc.concat(val), []);

		content.forEach((item) => {
			if (item.type === "text") {
				// item.value.split("[NEWLINE]").forEach((line, idx, arr) => {
				// 	if (line !== "") {
				// 		const textNode = document.createTextNode(line);
				// 		contentEditableDiv.appendChild(textNode);
				// 	}
				// 	if (idx < arr.length - 1) {
				// 		const brElement = document.createElement("br");
				// 		contentEditableDiv.appendChild(brElement);
				// 	}
				// });
				const textNode = document.createTextNode(
					item.value.replace(/\[NEWLINE\]/g, "\n")
				);
				contentEditableDiv.appendChild(textNode);
			} else if (item.type === "req-text") {
				const textNode = document.createElement("span");
				textNode.id = item.id;
				const reqSpan = new RequirementSpan({
					target: textNode,
					props: {
						content: item.value,
						id: item.id,
					},
				});
				contentEditableDiv.appendChild(textNode);
			} else if (item.type === "tag") {
				const imgNode = document.createElement("span");
				const reqChip = new RequirementChip({
					target: imgNode,
					props: {
						name: item.value,
						id: item.id,
					},
				});
				contentEditableDiv.appendChild(imgNode);
			}
		});
	}

	function handleInput() {
		allowUpdates = true;
		requirements.update((reqs) => {
			Object.entries(reqs).forEach(([id, req]) => {
				const reqSpan = document.getElementById(id);
				if (reqSpan) {
					req.promptSnippet = reqSpan.textContent;
				}
			});
			return reqs;
		});
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
		if (e.key === "s" && e.metaKey) {
			e.preventDefault();
			updatePrompt();
		}
	}

	function handlePaste(event) {
		event.preventDefault();
		const clipboardData = event.clipboardData.getData("text");
		document.execCommand("insertHTML", false, clipboardData);
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
				content: "Update requirements.",
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
						<path fill="var(--G1)" d={mdiArrowUpBold} />
					{:else}
						<path fill="var(--G4)" d={mdiArrowUpBold} />
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
		line-height: 22px;
		white-space: pre-wrap;
	}
</style>
