<script lang="ts">
	import { columnHash } from "../util/util";
	import {
		currentPromptId,
		model,
		requirements,
		requirementUpdating,
		settings,
		status,
		suggestedRequirements,
	} from "../stores";
	import { ZenoColumnType, ZenoService } from "../zenoservice";
	import { clickOutside } from "../util/clickOutside";
	import RequirementEvalChip from "../metadata/chips/RequirementEvalChip.svelte";
	import { TrailingIcon } from "@smui/chips";
	import Paper, { Content } from "@smui/paper";
	import { Icon } from "@smui/button";
	import { InitialFocus } from "@smui/dialog";
	import type { Example } from "../zenoservice/models/prompt";

	export let example: Example;
</script>

<div class="box svelte-ohpquu">
	<span class="label svelte-ohpquu">input:</span>
	<span class="value svelte-ohpquu">
		{example.input}
	</span>
	<br />
	<span class="label svelte-ohpquu">output:</span>
	<span class="value svelte-ohpquu">
		{example.output}
	</span>
	<br />
	<span class="label svelte-ohpquu">feedback:</span>
	<span class="value svelte-ohpquu">
		{example.feedback}
	</span>
	<TrailingIcon
		class="material-icons"
		style="margin-bottom: 5px; margin-left: 0px; color: {example.isPositive
			? '#97ca00'
			: '#e05d44'};">
		{#if example.isPositive}
			thumb_up
		{:else}
			thumb_down
		{/if}
	</TrailingIcon>
</div>

<style>
	.label.svelte-ohpquu {
		font-size: 12px;
		color: rgba(0, 0, 0, 0.5);
		font-variant: small-caps;
	}
	.value.svelte-ohpquu {
		font-size: 12px;
		white-space: pre-wrap;
	}
	.box.svelte-ohpquu {
		padding: 10px;
		border: 0.5px solid rgb(224, 224, 224);
		margin: 1px;
	}
</style>
