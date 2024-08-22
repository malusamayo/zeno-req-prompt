<script lang="ts">
	import { mdiUpdate } from "@mdi/js";
	import IconButton, { Icon } from "@smui/icon-button";
	import { Svg } from "@smui/common";
	import { tooltip } from "@svelte-plugins/tooltips";
	import { prompts, currentPromptId, status } from "../stores";
	import { ZenoService } from "../zenoservice";
	import CircularProgress from "@smui/circular-progress";

	let prompt: string = $prompts.get($currentPromptId).text;
	let promptBeingUpdated = false;

	$: {
		$currentPromptId;
		switchPrompt();
	}

	let allowUpdates = false;

	function switchPrompt() {
		prompt = $prompts.get($currentPromptId).text;
	}

	function updatePrompt() {
		promptBeingUpdated = true;
		ZenoService.createNewPrompt({ text: prompt, version: "" }).then(() => {
			ZenoService.getCurrentPromptId().then((res) => {
				ZenoService.getCompleteColumns().then((cols) => {
					status.update((s) => {
						s.completeColumns = cols;
						return s;
					});
					currentPromptId.set(res[0]);
					prompts.update((pts) => {
						return pts.set(res[0], { text: prompt, version: res[0] });
					});
					promptBeingUpdated = false;
					allowUpdates = false;
				});
			});
		});
	}
</script>

<div class="inline">
	<div class="inline">
		<h4>Prompt</h4>
		{#if promptBeingUpdated}
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
<textarea
	bind:value={prompt}
	on:input={() => {
		allowUpdates = true;
	}} />

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
</style>
