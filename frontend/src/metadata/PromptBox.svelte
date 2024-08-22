<script lang="ts">
	import { mdiUpdate } from "@mdi/js";
	import IconButton, { Icon } from "@smui/icon-button";
	import { Svg } from "@smui/common";
	import { tooltip } from "@svelte-plugins/tooltips";
	import { prompts, currentPromptId } from "../stores";
	import { ZenoService } from "../zenoservice";

	let prompt: string = $prompts.get($currentPromptId).text;

	$: {
		$currentPromptId;
		switchPrompt();
	}

	let showSubmitButton = false;

	function switchPrompt() {
		prompt = $prompts.get($currentPromptId).text;
	}

	function updatePrompt() {
		ZenoService.createNewPrompt({ text: prompt, version: "" }).then(() => {
			ZenoService.getCurrentPromptId().then((res) => {
				currentPromptId.set(res[0]);
				prompts.update((pts) => {
					return pts.set(res[0], { text: prompt, version: res[0] });
				});
			});
		});
	}
</script>

<div class="inline">
	<div class="inline">
		<h4>Prompt</h4>
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
					updatePrompt();
				}}>
				<Icon component={Svg} viewBox="0 0 24 24">
					{#if showSubmitButton}
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
		showSubmitButton = true;
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
