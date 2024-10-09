<script lang="ts">
	import { Icon } from "@smui/icon-button";
	import Paper, { Content } from "@smui/paper";
	import { clickOutside } from "../../util/clickOutside";
	import type { Requirement } from "src/zenoservice";
	import {
		currentPromptId,
		prompts,
		requirements,
		requirementToEdit,
		showNewFolder,
		showNewRequirement,
		showNewSlice,
		showSliceFinder,
        requirementUpdating,
        model,
	} from "../../stores";
    import { ZenoColumnType, ZenoService } from "../../zenoservice";

	// export let requirement: Requirement;
	export let name; // = requirement.name;
	export let id;
    export let exampleId;
    export let feedbackPositive;
	let requirement: Requirement;
	let showOptions = false;
	let menuX = 0;
	let menuY = 0;
    let isBadClicked = false;
    let isGoodClicked = false;

	$: {
		name;
		requirement = $requirements[id];
        $model;
        $currentPromptId;
	}
	$:srcLink = `https://img.shields.io/badge/${name.replaceAll(
		"-",
		"--"
	)}-${
		isBadClicked ? "e05d44" : isGoodClicked ? "97ca00" : "a463f2"
	}`; // Red if bad clicked, green if good clicked, purple otherwise

    function feedbackToRequirements() {
		requirementUpdating.set(true);
		ZenoService.updateReqFeedback({
			model: $model,
			promptId: $currentPromptId,
			exampleId: exampleId,
			isPositive: feedbackPositive,
			feedback: '',
            requirementId: id,
		}).then((newRequirements) => {
			requirements.set(newRequirements);
			requirementUpdating.set(false);
		});
	}

	function handleSpanClick(event) {
		// const spanRect = event.target.getBoundingClientRect();
		// menuX = spanRect.left;
		// menuY = spanRect.bottom;
		// showOptions = !showOptions;
		if (requirement == null) {
			return;
		}

		showNewSlice.set(false);
		showNewFolder.set(false);
		showSliceFinder.set(false);
		// showNewRequirement.update((d) => !d);
        feedbackToRequirements()
        if (feedbackPositive) {
            isGoodClicked = true;
        }
        if (!feedbackPositive){
            isBadClicked = true;
        }
		requirementToEdit.set(requirement);
	}
</script>

<span>
	<img
		class="tag"
		draggable="false"
		src={srcLink}
		alt=""
		data={name}
		on:click={handleSpanClick}
		on:keydown={() => {}} />
</span>

<style>
	.tag {
		cursor: pointer;
		/* pointer-events: none; */
		margin-right: 2px;
		margin-bottom: -2.5px;
	}
</style>
