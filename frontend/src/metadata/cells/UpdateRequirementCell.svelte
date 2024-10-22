


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
    import {
        reports,
        selections,
        showNewSlice,
        sliceToEdit,
        slices,
        model,
        comparisonModel,
        showNewRequirement,
        showNewFolder,
        showSliceFinder,
        requirementToEdit,
        requirements,
        requirementUpdating,
        currentPromptId,
        promptToUpdate,
        suggestedRequirements,
        requirementAddedExample,
    } from "../../stores";
    // import { clickOutside } from "../../util/clickOutside";
    import { ZenoService, type Slice, type Requirement } from "../../zenoservice";
    // import RequirementCellResult from "./RequirementCellResult.svelte";
    import UpdateRequirementChip from "../chips/UpdateRequirementChip.svelte";
    import { onMount } from 'svelte';
    // import { TrailingIcon } from "@smui/chips";

    export let requirement: Requirement;
    export let exampleId;
    export let feedbackPositive;
    
    onMount(() => {
		console.log(parseInt($currentPromptId[1], 10));
        requirementAddedExample.subscribe(pairs => {
            // Check if the array [req_id, example_id] exists in the store
            isChecked = pairs.some(pair => pair[0] === requirement.id && pair[1] === exampleId && pair[2] === feedbackPositive && parseInt(pair[3], 10) === parseInt($currentPromptId[1], 10));
        });
    });

    $: {
        requirement;
        $model;
        $currentPromptId;
    }
    function feedbackToRequirements() {
        requirementUpdating.set(true);
        ZenoService.updateReqFeedback({
            model: $model,
            promptId: $currentPromptId,
            exampleId: String(exampleId),
            isPositive: feedbackPositive,
            feedback: '',
            requirementId: requirement.id,
        }).then((newRequirements) => {
            requirements.set(newRequirements);
            requirementUpdating.set(false);
        })
    }

    function removeExample() {
        requirementUpdating.set(true);
        ZenoService.removeExample({
            promptId: $currentPromptId,
            exampleId: String(exampleId),
            requirementId: requirement.id,
        }).then((newRequirements) => {
            requirements.set(newRequirements);
            requirementUpdating.set(false);
        });
    }
    let isChecked = false;
    let req_id = requirement.id;


    // Function to toggle the checkbox state and update the store
    function toggleChecked() {
        isChecked = !isChecked; // Toggle the checked state first
        requirementAddedExample.update(pairs => {
            if (isChecked) {
                // If checked, remove the array from the store
                removeExample();
                // requirement.examples = requirement.examples.filter(example => example.id !== exampleId);
                return pairs.filter(pair => !(pair[0] === req_id && pair[1] === exampleId && pair[2] === feedbackPositive) && parseInt(pair[3], 10) === parseInt($currentPromptId[1], 10));
            } else {
                // If unchecked, add the array [req_id, example_id] to the store
                feedbackToRequirements();
                return [...pairs, [req_id, exampleId, feedbackPositive,$currentPromptId[1]]];
            }
        });
    }
</script>

<div
    class=" cell parent">

    <div class="group" style:width="100%">
        <div class="group" style:width="100%">
            <div class="inline">
                <div class="hori-group" style:color="var(--G1)">
                    <UpdateRequirementChip name={requirement.name} id={requirement.id} exampleId={exampleId} feedbackPositive={feedbackPositive}/>
                    <div class="requirement-box">
                        <!-- Description and checkbox side by side -->
                        <div class="description">
                            {requirement.description}
                        </div>
                        <input type="checkbox" class="requirement-checkbox" bind:checked={isChecked} on:change={toggleChecked} />
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
    .requirement-box {
        display: flex;
        align-items: center; /* Vertically center the checkbox */
        justify-content: space-between; /* Space between description and checkbox */
    }
    .requirement-checkbox {
        margin-left: 10px; /* Optional: add a bit of space */
    }

</style>

