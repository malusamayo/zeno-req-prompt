<script lang="ts">
	import {
		mdiCogs,
		mdiCreation,
		mdiCreationOutline,
		mdiFolderPlusOutline,
		mdiInformationOutline,
		mdiMagicStaff,
		mdiPlus,
		mdiPlusCircle,
	} from "@mdi/js";
	import Button from "@smui/button";
	import CircularProgress from "@smui/circular-progress";
	import { Svg } from "@smui/common";
	import IconButton, { Icon } from "@smui/icon-button";
	import { tooltip } from "@svelte-plugins/tooltips";
	import { InternMap } from "internmap";
	import {
		getHistogramCounts,
		getHistogramMetrics,
		getHistograms,
		type HistogramEntry,
	} from "../api/metadata";
	import { createNewTag } from "../api/tag";
	import {
		editId,
		editedIds,
		folders,
		folderToEdit,
		metric,
		metricRange,
		model,
		comparisonModel,
		requestingHistogramCounts,
		selectionIds,
		selectionPredicates,
		selections,
		showNewFolder,
		showNewSlice,
		showNewTag,
		showSliceFinder,
		sliceToEdit,
		slices,
		status,
		tagIds,
		tags,
		tab,
		promptUpdating,
		prompts,
		currentPromptId,
		showNewRequirement,
	} from "../stores";
	import { columnHash, updateModelDependentSlices } from "../util/util";
	import { ZenoColumnType, type ZenoColumn } from "../zenoservice";
	import MetricRange from "./MetricRange.svelte";
	import FolderCell from "./cells/FolderCell.svelte";
	import MetadataCell from "./cells/MetadataCell.svelte";
	import SliceCell from "./cells/SliceCell.svelte";
	import TagCell from "./cells/TagCell.svelte";
	import MetadataHeader from "./MetadataHeader.svelte";
	import SliceCellResult from "./cells/SliceCellResult.svelte";
	import PromptBox from "./PromptBox.svelte";
	import RequirementPanel from "./RequirementPanel.svelte";
	import ItemView from "../instance-views/ItemView.svelte";
</script>

<div class="side-container">
	<div class="inline">
		<h4>Task description</h4>
	</div>
	<textarea />

	<RequirementPanel />

	<div class="inline">
		<h4>Sampled example</h4>

		<div class="inline">
			<div
				use:tooltip={{
					content: "Brainstorm requirements.",
					position: "left",
					theme: "zeno-tooltip",
				}}>
				<IconButton on:click={() => {}} style="cursor:pointer; margin-top:-5px">
					<Icon class="material-icons">refresh</Icon>
				</IconButton>
			</div>
		</div>
	</div>
	<!-- <ItemView item={inst} /> -->

	<!-- <PromptBox /> -->
</div>
<div class="side-container-examples">
	<div class="inline">
		<h4>Saved examples</h4>
	</div>
	<!-- <ItemView item={inst2} />
	<ItemView item={inst3} /> -->
</div>

<style>
	.side-container {
		width: 800px;
		min-width: 800px;
		max-width: 800px;
		padding-top: 10px;
		padding-bottom: 50px;
		padding-left: 15px;
		padding-right: 10px;
		/* overflow-y: scroll; */
		background-color: var(--Y2);
	}
	.side-container-examples {
		width: 300px;
		min-width: 300px;
		max-width: 300px;
		padding-top: 10px;
		padding-bottom: 50px;
		padding-left: 15px;
		padding-right: 10px;
		/* overflow-y: scroll; */
		background-color: var(--Y2);
	}
	.inline {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}
	.compare-slice-cell {
		padding-top: 5px;
		padding-bottom: 5px;
	}
	.overview {
		display: flex;
		align-items: center;
		border: 1px solid var(--G5);
		border-radius: 4px;
		padding-left: 10px;
		justify-content: space-between;
		padding-right: 10px;
		min-height: 36px;
		cursor: pointer;
		color: var(--G1);
	}
	.selected {
		background: var(--P3);
	}
	.information-tooltip {
		width: 24px;
		height: 24px;
		cursor: help;
		fill: var(--G2);
	}
	textarea {
		width: calc(100% - 20px); /* Adjust width to account for padding */
		padding: 8px;
		position: relative;
		overflow: visible;
		border: 0.5px solid var(--G4);
		border-radius: 4px;
		margin-top: 5px;
		display: flex;
		padding-left: 5px;
		padding-right: 10px;
		min-height: 36px;
		min-width: 200px;
		font-size: small;
		font-weight: lighter;
		resize: none;
	}
</style>
