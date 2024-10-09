<script lang="ts">
	// import { mdiDotsHorizontal, mdiCheckOutline } from "@mdi/js";
	// import Button, { Label } from "@smui/button";
	// import { Svg } from "@smui/common";
	// import Dialog, { Actions, Content, InitialFocus, Title } from "@smui/dialog";
	// import IconButton, { Icon } from "@smui/icon-button";
	// import Paper from "@smui/paper";
	// import { deleteSlice, doesModelDependOnPredicates } from "../../api/slice";
	// import { selectSliceCell } from "./sliceCellUtil";
	// import SliceDetails from "../../general/SliceDetails.svelte";
	// import SliceCellResult from "./SliceCellResult.svelte";
	// import {
	// 	reports,
	// 	selections,
	// 	showNewSlice,
	// 	sliceToEdit,
	// 	slices,
	// 	model,
	// 	comparisonModel,
	// 	showNewRequirement,
	// 	showNewFolder,
	// 	showSliceFinder,
	// 	requirementToEdit,
	// 	requirements,
	// 	promptToUpdate,
	// 	suggestedRequirements,
	// } from "../../stores";
	// import { clickOutside } from "../../util/clickOutside";
	import { ZenoService, type Slice, type Requirement } from "../../zenoservice";
	// import RequirementCellResult from "./RequirementCellResult.svelte";
	import UpdateRequirementChip from "../chips/UpdateRequirementChip.svelte";
	// import { TrailingIcon } from "@smui/chips";

	export let requirement: Requirement;
	export let exampleId;
	export let feedbackPositive;

</script>

<div
	class=" cell parent">

	<div class="group" style:width="100%">
		<div class="group" style:width="100%">
			<div class="inline">
				<div class="hori-group" style:color="var(--G1)">
					<UpdateRequirementChip name={requirement.name} id={requirement.id} exampleId={exampleId} feedbackPositive={feedbackPositive}/>
					<div
						class="description">
						{requirement.description}
					</div>
				</div>
			</div>
		
		</div>
	</div>
</div>

<style>
	.cell {
		position: relative;
		overflow: visible;
		border: 0.5px solid var(--G4);
		border-radius: 4px;
		margin-top: 5px;
		display: flex;
		padding-left: 10px;
		padding-right: 10px;
		min-height: 36px;
	}
	.group {
		display: flex;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
	}
	.hori-group {
		flex-direction: row;
		align-items: center;
		margin-top: 5px;
		margin-bottom: 5px;
	}
	.description {
		font-size: normal;
		font-weight: lighter;
		cursor: text;
		margin-left: -5px;
		padding-left: 5px;
		padding-right: 5px;
	}
</style>
