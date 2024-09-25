<script lang="ts">
	import IconButton, { Icon } from "@smui/icon-button";
	import { Svg } from "@smui/common";
	import { tooltip } from "@svelte-plugins/tooltips";
	import Dialog, { Actions, Content, InitialFocus, Title } from "@smui/dialog";
	import Button, { Label } from "@smui/button";

	import {
		metric,
		metrics,
		model,
		models,
		comparisonModel,
		tab,
		prompts,
		currentPromptId,
		status,
	} from "../stores";
	import { mdiPlayOutline } from "@mdi/js";
	import { ZenoService } from "../zenoservice";

	let confirmRunPrompt = false;

	$: exludeModels = $models.filter((m) => m !== $model);
	$: promptIds = Array.from($prompts.keys());

	function runPrompt() {
		status.update((s) => {
			s.status = "Running inference";
			return s;
		});
		ZenoService.runPrompt({ model: $model, promptId: $currentPromptId }).then(
			() => {
				ZenoService.getCompleteColumns().then((cols) => {
					status.update((s) => {
						s.status = "Done processing";
						s.completeColumns = cols;
						return s;
					});
				});
			}
		);
	}
</script>

<div class="inline">
	<div id="selections">
		{#if $model !== undefined}
			<div style="margin-right: 10px;">
				<div class="options-header">
					{$tab === "comparison" ? "Model A" : "Model"}
				</div>
				<select bind:value={$model}>
					{#each $models as mod}
						<option value={mod}>{mod}</option>
					{/each}
				</select>
			</div>
		{/if}
		{#if $tab !== "comparison" && $metric !== undefined}
			<!-- <div>
			<div class="options-header">Metric</div>
			<select bind:value={$metric}>
				{#each $metrics as met}
					<option value={met}>{met}</option>
				{/each}
			</select>
		</div> -->
			<div>
				<div class="options-header">Prompt</div>
				<select bind:value={$currentPromptId}>
					{#each promptIds as pid}
						<option value={pid}>{pid}</option>
					{/each}
				</select>
			</div>
		{/if}
		{#if $tab === "comparison"}
			<div>
				<div class="options-header">Model B</div>
				<select bind:value={$comparisonModel}>
					{#each exludeModels as mod}
						<option value={mod}>{mod}</option>
					{/each}
				</select>
			</div>
		{/if}
	</div>
	<div
		use:tooltip={{
			content: "Start inference",
			position: "left",
			theme: "zeno-tooltip",
		}}
		style="margin-top:10px">
		<IconButton
			on:click={() => {
				confirmRunPrompt = true;
			}}
			style="cursor:pointer">
			<Icon component={Svg} viewBox="0 0 24 24">
				<path fill="var(--G1)" d={mdiPlayOutline} />
			</Icon>
		</IconButton>
	</div>
</div>
{#if $tab === "comparison" && $metric !== undefined}
	<div>
		<div class="options-header">Metric</div>
		<select style="width: 345px" bind:value={$metric}>
			{#each $metrics as met}
				<option value={met}>{met}</option>
			{/each}
		</select>
	</div>
{/if}

<Dialog
	bind:open={confirmRunPrompt}
	scrimClickAction=""
	escapeKeyAction=""
	aria-labelledby="delete-slice"
	aria-describedby="delete-slice">
	<Title id="simple-title">Run prompt</Title>
	<Content id="simple-content">Run prompt on all examples. Continue?</Content>
	<Actions>
		<Button
			on:click={() => {
				confirmRunPrompt = false;
			}}>
			<Label>No</Label>
		</Button>
		<Button use={[InitialFocus]} on:click={() => runPrompt()}>
			<Label>Yes</Label>
		</Button>
	</Actions>
</Dialog>

<style>
	.inline {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}
	select {
		width: 167px;
		height: 35px;
		border: 1px solid var(--G4);
		border-radius: 4px;
		font-size: 14px;
		color: var(--G1);
	}
	option {
		padding: 5px;
	}
	option:checked {
		background-color: var(--G5);
	}
	.options-header {
		margin-top: 5px;
		margin-bottom: 5px;
		color: var(--G2);
	}
	#selections {
		display: flex;
		flex-direction: row;
		align-items: center;
		padding-bottom: 10px;
		padding-top: 5px;
	}
	.options-header {
		margin-top: 5px;
		margin-bottom: 5px;
		color: var(--G2);
	}
</style>
