<script lang="ts">
	import Button from "@smui/button";
	import Paper, { Content } from "@smui/paper";
	import Textfield from "@smui/textfield";
	import {
		folders,
		folderToEdit,
		goals,
		showNewGoal,
		slices,
	} from "../../stores";
	import { clickOutside } from "../../util/clickOutside";
	import { ZenoService, type Requirement } from "../../zenoservice";

	let goalName = "";
	let input;
	let originalGoalName = "";

	$: invalidName =
		($folders.includes(goalName) && goalName !== originalGoalName) ||
		goalName.length === 0;

	$: if ($showNewGoal && input) {
		input.getElement().focus();
	}

	$: if ($folderToEdit) {
		originalGoalName = $folderToEdit;
		goalName = $folderToEdit;
	}

	function createGoal() {
		if ($folderToEdit) {
			slices.update((sls) => {
				let inFolder = [...sls.values()].filter(
					(d) => d.folder === originalGoalName
				);
				inFolder.forEach((slice) => {
					slice.folder = goalName;
					sls.set(slice.sliceName, slice);
					ZenoService.createNewSlice({
						sliceName: slice.sliceName,
						filterPredicates: slice.filterPredicates,
						folder: slice.folder,
					});
				});
				return sls;
			});
			folders.update((f) => {
				f[f.indexOf(originalGoalName)] = goalName;
				return f;
			});
			folderToEdit.set(undefined);
		} else {
			goals.update((f) => {
				if (!f.includes(goalName)) {
					if (f[f.length - 1] === "uncategorized") {
						f.pop();
						f.push(goalName);
						f.push("uncategorized");
					} else {
						f.push(goalName);
					}
				}
				return [...f];
			});
		}

		showNewGoal.set(false);
	}

	/** Define keyboard action **/
	function submit(e) {
		if ($showNewGoal && e.key === "Escape") {
			showNewGoal.set(false);
		}
		if ($showNewGoal && e.key === "Enter" && !invalidName) {
			createGoal();
		}
	}
</script>

<svelte:window on:keydown={submit} />

<div
	id="paper-container"
	use:clickOutside
	on:click_outside={() => showNewGoal.set(false)}>
	<Paper elevation={7}>
		<Content style="display: flex; align-items: center;">
			<Textfield bind:value={goalName} label="Goal Name" bind:this={input} />
			<Button
				style="margin-left: 10px;"
				variant="outlined"
				on:click={() => showNewGoal.set(false)}>
				Cancel
			</Button>
			<Button
				style="margin-left: 5px;"
				variant="outlined"
				disabled={invalidName}
				on:click={() => createGoal()}>
				{$folderToEdit ? "Update" : "Create"}
			</Button>
		</Content>
		{#if invalidName && goalName.length > 0}
			<p style:margin-right="10px" style:color="red">folder already exists</p>
		{/if}
	</Paper>
</div>

<style>
	#paper-container {
		position: fixed;
		left: 580px;
		top: 200px;
		z-index: 20;
	}
</style>
