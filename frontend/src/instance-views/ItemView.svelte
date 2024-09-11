<script lang="ts">
	import { columnHash } from "../util/util";
	import {
		currentPromptId,
		model,
		requirements,
		settings,
		status,
	} from "../stores";
	import { ZenoColumnType } from "../zenoservice";
	import RequirementEvalChip from "../metadata/chips/RequirementEvalChip.svelte";

	export let item;
	let modelColumn;
	let evalColumns;
	let rationaleColumns;

	let requirementIds;

	$: {
		$model;
		$currentPromptId;

		let obj = $status.completeColumns.find((c) => {
			return (
				c.columnType === ZenoColumnType.OUTPUT &&
				c.model === $model &&
				c.promptId === $currentPromptId
			);
		});
		modelColumn = obj ? columnHash(obj) : "";

		evalColumns = $status.completeColumns
			.filter((c) => {
				return (
					c.columnType === ZenoColumnType.POSTDISTILL &&
					c.model === $model &&
					c.promptId === $currentPromptId &&
					!c.name.includes("Rationale")
				);
			})
			.reduce((acc, col) => {
				let reqId = col.name.replace("evalR", "");
				return { ...acc, [reqId]: columnHash(col) };
			}, {});

		rationaleColumns = $status.completeColumns
			.filter((c) => {
				return (
					c.columnType === ZenoColumnType.POSTDISTILL &&
					c.model === $model &&
					c.promptId === $currentPromptId &&
					c.name.includes("Rationale")
				);
			})
			.reduce((acc, col) => {
				let reqId = col.name.replace("evalR", "").replace("Rationale", "");
				return { ...acc, [reqId]: columnHash(col) };
			}, {});

		requirementIds = Object.keys($requirements);
	}
</script>

<div class="box svelte-ohpquu">
	<span class="label svelte-ohpquu">input:</span>
	<span class="value svelte-ohpquu">
		{item[columnHash($settings.dataColumn)]}
	</span>
	{#if modelColumn !== ""}
		<br />
		<span class="label svelte-ohpquu">output:</span>
		<span class="value svelte-ohpquu">
			{item[modelColumn]}
		</span>
	{/if}
	{#if Object.keys(evalColumns).length > 0}
		<br />
		{#each requirementIds as reqId}
			<RequirementEvalChip
				id={reqId}
				isPass={item[evalColumns[reqId]] === true}
				rationale={item[rationaleColumns[reqId]]} />
		{/each}
	{/if}
</div>

<style>
	.label.svelte-ohpquu {
		font-size: 12px;
		color: rgba(0, 0, 0, 0.5);
		font-variant: small-caps;
	}
	.value.svelte-ohpquu {
		font-size: 12px;
	}
	.box.svelte-ohpquu {
		padding: 10px;
		border: 0.5px solid rgb(224, 224, 224);
		margin: 1px;
	}
</style>
