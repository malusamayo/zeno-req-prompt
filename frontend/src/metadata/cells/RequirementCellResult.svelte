<script lang="ts">
	import {
		metric,
		status,
		selections,
		model,
		settings,
		currentPromptId,
	} from "../../stores";
	import { columnHash } from "../../util/util";
	import {
		getMetricsForSlices,
		doesModelDependOnPredicates,
	} from "../../api/slice";
	import { selectModelDependSliceCell } from "./sliceCellUtil";
	import {
		ZenoColumnType,
		type MetricKey,
		type Requirement,
		type Slice,
		type FilterPredicate,
		type ZenoColumn,
	} from "../../zenoservice";
	import { VegaLite } from "svelte-vega";
	import { generateStackedBarChartSpec } from "../../report/bar-chart/vegaSpec-bar";

	export let compare;
	export let requirement: Requirement;

	let result;

	let slice = {
		sliceName: "",
		folder: "",
		filterPredicates: { predicates: [], join: "" },
	};

	$: modelDependSliceName = "";

	$: compareButton = false;

	$: selected = false;
	// $selections.slices.includes(slice.sliceName) ||
	// $selections.slices.includes(modelDependSliceName);

	$: outputColumns = $status.completeColumns.filter(
		(c) =>
			c.name === `evalR${requirement.id}` && c.promptId === $currentPromptId
	);

	$: {
		$currentPromptId;
		result = null;
	}

	$: {
		$status;
		// if ($status.completeColumns.map((c) => c.name).includes("model")) {
		// 	compareButton = doesModelDependOnPredicates(
		// 		requirement.filterPredicates.predicates
		// 	);
		// }
		if (outputColumns.length > 0) {
			result = getMetricsForSlices([
				<MetricKey>{
					sli: slice,
					model: $model,
					metric: $metric,
					promptId: $currentPromptId,
					requirementId: requirement.id,
				},
			]);
		}
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

	function prepareBarChartData(passed, failed) {
		return [
			{ category: "Pass", value: passed },
			{ category: "Fail", value: failed },
		];
	}

	// function handleBarClick(clickedCategory: string) {
	// 	console.log("clicked")
	// 	// Create a new FilterPredicate using the correct ZenoColumn
	// 	let newPredicate: FilterPredicate = {
	// 		column: outputColumns[0], // Use the dynamically created ZenoColumn object
	// 		operation: "==", // The operation for the filter
	// 		value: true, // Set value based on clicked category (Pass = 1, Fail = 0)
	// 		join: "", // Optional join logic
	// 	};

	// 	// Update the selections with the new filter predicate for the corresponding requirement
	// 	selections.update((mets) => ({
	// 		slices: mets.slices,
	// 		metadata: {
	// 			...mets.metadata,
	// 			[columnHash(outputColumns[0])]: {
	// 				predicates: [newPredicate], // Array of FilterPredicate
	// 				join: "" // Logic for joining predicates (if needed)
	// 			}
	// 		},
	// 		tags: mets.tags,
	// 	}));
	// }

	const handleBarClick = (name, value) => {
		// Check if value and category are defined and log the clicked category
		if (value && value.category && value.category[0]) {
			// console.log("clicked:", value.category[0]); // Debug line

			// Check if the category is "Pass" or "Fail"
			let newPredicate;

			if (value.category[0] === "Pass") {
				newPredicate = {
					column: outputColumns[0], // Use the first ZenoColumn object in outputColumns
					operation: "==", // The operation for the filter
					value: true, // Set value based on clicked category (Pass = true)
					join: "", // Optional join logic
				};
			} else if (value.category[0] === "Fail") {
				newPredicate = {
					column: outputColumns[0], // Use the first ZenoColumn object in outputColumns
					operation: "==", // The operation for the filter
					value: false, // Set value based on clicked category (Fail = false)
					join: "", // Optional join logic
				};
			}

			let predicates: FilterPredicate[] = [newPredicate];
			// Further logic to apply or use `newPredicate`
			// console.log("New filter predicate:", newPredicate); // Debugging newPredicate

			selections.update((mets) => ({
				slices: mets.slices,
				metadata: {
					...mets.metadata,
					[columnHash(outputColumns[0])]: { predicates, join: "" },
				},
				tags: mets.tags,
			}));
		}
	};
</script>

{#if result}
	{#await result then res}
		<div
			class={"compare " + compareButtonstyle}
			on:keydown={() => ({})}
			on:click={selectFilter}>
			<span>
				<!-- {res[0].metric !== undefined && res[0].metric !== null
					? res[0].metric.toFixed(2)
					: ""} -->
				<!-- <VegaLite spec={generateStackedBarChartSpec(prepareBarChartData(res[0].metric, 1 - res[0].metric))} 
				options={{ actions: false }} /> -->
				<VegaLite
					spec={generateStackedBarChartSpec(
						prepareBarChartData(res[0].metric, 1 - res[0].metric)
					)}
					options={{ actions: false }}
					signalListeners={{ barSelect: handleBarClick }} />
			</span>
			<!-- <span id="size">
				({res[0].size.toLocaleString()})
			</span> -->
		</div>
	{/await}
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
		margin-right: 30px;
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
