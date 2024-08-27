<script lang="ts">
	import { metric, status, selections, model, settings } from "../../stores";
	import {
		getMetricsForSlices,
		doesModelDependOnPredicates,
	} from "../../api/slice";
	import { selectModelDependSliceCell } from "./sliceCellUtil";
	import {
		type MetricKey,
		type Requirement,
		type Slice,
	} from "../../zenoservice";

	export let compare;
	export let requirement: Requirement;

	let result;

	let res = [{ metric: Math.random(), size: $settings.totalSize }];

	$: modelDependSliceName = "";

	$: compareButton = false;

	$: selected = false;
	// $selections.slices.includes(slice.sliceName) ||
	// $selections.slices.includes(modelDependSliceName);

	$: {
		$status;
		// result = getMetricsForSlices([
		// 	<MetricKey>{
		// 		sli: slice,
		// 		model: sliceModel,
		// 		metric: $metric,
		// 	},
		// ]);
	}

	$: compareButtonstyle = compareButton
		? "compare-btn " + (selected ? "selected" : "")
		: "";

	function selectFilter(e) {
		if (compare && compareButton) {
			e.stopPropagation();
			selectModelDependSliceCell(modelDependSliceName);
		}
	}
</script>

{#if res}
	<!-- {#await result then res} -->
	<div
		class={compare ? "compare " + compareButtonstyle : "flex-row"}
		on:keydown={() => ({})}
		on:click={selectFilter}>
		<span>
			{res[0].metric !== undefined && res[0].metric !== null
				? res[0].metric.toFixed(2)
				: ""}
		</span>
		<span id="size">
			({res[0].size.toLocaleString()})
		</span>
	</div>
	<!-- {/await} -->
{/if}

<style>
	.flex-row {
		display: flex;
		align-items: center;
	}
	span {
		width: 50px;
		margin-right: 5px;
		text-align: right;
	}
	#size {
		font-style: italic;
		color: var(--G3);
	}
	.compare {
		display: flex;
		flex-direction: column;
		align-items: center;
		margin-right: 10px;
		padding: 1px;
	}
	.compare-btn {
		border: 0.5px solid var(--G4);
		border-radius: 5px;
	}
	.compare-btn:hover {
		cursor: pointer;
		box-shadow: 0px 1px 2px 0px var(--G4);
	}
	.selected {
		background: var(--P3);
	}
</style>
