<script lang="ts">
	import { Icon, Label } from "@smui/button";
	import Checkbox from "@smui/checkbox";
	import { Pagination } from "@smui/data-table";
	import IconButton from "@smui/icon-button";
	import Select, { Option } from "@smui/select";
	import { tick } from "svelte";
	import { getFilteredTable } from "../api/table";
	import { setModelForFilterPredicateGroup } from "../api/slice";
	import {
		editId,
		editedIds,
		model,
		rowsPerPage,
		selectionIds,
		selectionPredicates,
		selections,
		settings,
		sort,
		status,
		tagIds,
		tags,
		currentPromptId,
	} from "../stores";
	import { columnHash } from "../util/util";
	import type { ZenoColumn } from "../zenoservice";
	import { MetadataType, ZenoColumnType } from "../zenoservice";
	import type { ViewRenderFunction } from "./instance-views";

	export let currentResult;
	export let viewFunction: ViewRenderFunction;
	export let viewOptions = {};

	let table;
	let viewDivs = {};
	let columnHeader: ZenoColumn[] = [];
	let body: HTMLElement;
	let currentTagIds = [];

	let currentPage = 0;
	let end = 0;
	let lastPage = 0;

	let sampleOptions = [5, 15, 30, 60, 100, $settings.samples].sort(
		(a, b) => a - b
	);

	$: idHash = columnHash($settings.idColumn);
	$: start = currentPage * $rowsPerPage;
	$: end = Math.min(start + $rowsPerPage, $settings.totalSize);
	$: currentResult.then((r) => {
		lastPage = Math.max(Math.ceil(r[0].size / $rowsPerPage) - 1, 0);
	});
	$: if (currentPage > lastPage) {
		currentPage = lastPage;
	}

	if ($editId !== undefined) {
		currentTagIds = $tags.get($editId).selectionIds.ids;
	}

	$: {
		currentTagIds;
		editedIds.set(currentTagIds);
	}

	// update on page, metadata selection, slice selection, or state change.
	$: {
		currentPage;
		$status.completeColumns;
		$selections.tags;
		$selectionPredicates;
		$model;
		$sort;
		$editId;
		$rowsPerPage;
		$currentPromptId;
		updateTable();
	}

	$: {
		viewFunction;
		table;
		$sort;
		viewOptions;
		drawInstances();
	}

	// Reset pagination on metadata selection or slice selection.
	selectionPredicates.subscribe(() => (currentPage = 0));

	function updateTable() {
		getFilteredTable(
			$status.completeColumns,
			[$model],
			[$currentPromptId],
			undefined,
			setModelForFilterPredicateGroup($selectionPredicates, $model),
			[start, end],
			$sort,
			$tagIds,
			$selectionIds,
			$selections.tags
		).then((res) => {
			table = res;
			if (body) {
				body.scrollTop = 0;
			}
		});
	}

	function updateSort(columnName) {
		if ($sort[0] !== columnName) {
			sort.set([columnName, true]);
		} else if ($sort[0] === columnName && $sort[1] === true) {
			sort.set([columnName, false]);
		} else {
			sort.set([undefined, true]);
		}
	}

	async function drawInstances() {
		if (!table) {
			return;
		}

		let obj = $status.completeColumns.find((c) => {
			return (
				c.columnType === ZenoColumnType.OUTPUT &&
				c.model === $model &&
				c.promptId === $currentPromptId
			);
		});
		let modelColumn = obj ? columnHash(obj) : "";

		columnHeader = $status.completeColumns.filter(
			(c) =>
				(c.model === "" || c.model === $model) &&
				(c.columnType === ZenoColumnType.METADATA ||
					c.columnType === ZenoColumnType.PREDISTILL ||
					c.columnType === ZenoColumnType.POSTDISTILL) &&
				$settings.dataColumn.name !== c.name &&
				$settings.labelColumn.name !== c.name
		);

		if (!viewFunction) {
			return;
		}

		await tick();

		table.forEach((_, i) => {
			let div = viewDivs[i];
			if (div) {
				viewFunction(
					div,
					viewOptions,
					table[i],
					modelColumn,
					columnHash($settings.labelColumn),
					columnHash($settings.dataColumn),
					idHash
				);
			}
		});
	}
</script>

{#if table}
	<div class="sample-container" bind:this={body}>
		<table id="column-table">
			<thead>
				<tr>
					{#if $editId !== undefined}
						<th>Included</th>
					{/if}
					{#if viewFunction}
						<th>instance</th>
					{/if}
					{#each columnHeader as header}
						{#if header.name !== $settings.idColumn.name && header.name !== $settings.dataColumn.name}
							<th on:click={() => updateSort(header)}>
								<div class="inline-header">
									{header.name}
									<Icon
										class="material-icons"
										style="font-size: 14px; padding-top:3px; margin-left: 5px;">
										{#if $sort[0] && $sort[0].name === header.name && $sort[1]}
											keyboard_arrow_down
										{:else if $sort[0] && $sort[0].name === header.name}
											keyboard_arrow_up
										{/if}
									</Icon>
								</div>
							</th>
						{/if}
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each table as tableContent, i (tableContent[idHash])}
					<tr>
						{#if $editId !== undefined}
							<td
								><Checkbox
									bind:group={currentTagIds}
									value={String(
										tableContent[columnHash($settings.idColumn)]
									)} /></td>
						{/if}
						{#if viewFunction}
							<td>
								<div bind:this={viewDivs[i]} />
							</td>
						{/if}
						{#each columnHeader as header}
							{#if header.name !== $settings.idColumn.name && header.name !== $settings.dataColumn.name}
								{#if header.metadataType === MetadataType.CONTINUOUS}
									<td>{tableContent[columnHash(header)].toFixed(2)}</td>
								{:else}
									<td>{tableContent[columnHash(header)]}</td>
								{/if}
							{/if}
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
	<Pagination slot="paginate" class="pagination">
		<svelte:fragment slot="rowsPerPage">
			<Label>Rows Per Page</Label>
			<Select variant="outlined" bind:value={$rowsPerPage} noLabel>
				{#each sampleOptions as option}
					<Option value={option}>{option}</Option>
				{/each}
			</Select>
		</svelte:fragment>
		<svelte:fragment slot="total">
			{start + 1}-{#await currentResult then r}
				{Math.min(end, r ? r[0].size : end)} of
				{r ? r[0].size : ""}{/await}
		</svelte:fragment>

		<IconButton
			class="material-icons"
			action="first-page"
			title="First page"
			on:click={() => (currentPage = 0)}
			disabled={currentPage === 0}>first_page</IconButton>
		<IconButton
			class="material-icons"
			action="prev-page"
			title="Prev page"
			on:click={() => currentPage--}
			disabled={currentPage === 0}>chevron_left</IconButton>
		<IconButton
			class="material-icons"
			action="next-page"
			title="Next page"
			on:click={() => currentPage++}
			disabled={currentPage >= lastPage}>chevron_right</IconButton>
		<IconButton
			class="material-icons"
			action="last-page"
			title="Last page"
			on:click={() => (currentPage = lastPage)}
			disabled={currentPage >= lastPage}>last_page</IconButton>
	</Pagination>
{/if}

<style>
	.inline-header {
		display: flex;
	}
	.sample-container {
		height: calc(100vh - 180px);
		width: calc(100vw - 600px);
		overflow: scroll;
		align-content: baseline;
		border-bottom: 1px solid var(--G5);
		display: flex;
		flex-wrap: wrap;
		min-width: 75px;
	}
	th {
		text-align: left;
		border-bottom: 1px solid var(--G5);
		padding-bottom: 5px;
		margin-bottom: 20px;
		margin-right: 20px;
		top: 2px;
		position: sticky;
		background-color: var(--G6);
		min-width: 70px;
		margin-bottom: 5px;
		padding-right: 1.6vw;
		cursor: pointer;
		font-weight: 600;
		z-index: 5;
	}
	td {
		padding-right: 15px;
	}
</style>
