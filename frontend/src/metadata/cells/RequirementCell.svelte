<script lang="ts">
	import { mdiDotsHorizontal, mdiCheckOutline } from "@mdi/js";
	import Button, { Label } from "@smui/button";
	import { Svg } from "@smui/common";
	import Dialog, { Actions, Content, InitialFocus, Title } from "@smui/dialog";
	import IconButton, { Icon } from "@smui/icon-button";
	import Paper from "@smui/paper";
	import { deleteSlice, doesModelDependOnPredicates } from "../../api/slice";
	import { selectSliceCell } from "./sliceCellUtil";
	import SliceDetails from "../../general/SliceDetails.svelte";
	import SliceCellResult from "./SliceCellResult.svelte";
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
		promptToUpdate,
		suggestedRequirements,
		currentPromptId,
	} from "../../stores";
	import { clickOutside } from "../../util/clickOutside";
	import { ZenoService, type Slice, type Requirement } from "../../zenoservice";
	import RequirementCellResult from "./RequirementCellResult.svelte";
	import RequirementChip from "../chips/RequirementChip.svelte";
	import { TrailingIcon } from "@smui/chips";
	import CircularProgress from "@smui/circular-progress";

	export let requirement: Requirement;
	export let compare;
	export let suggested;

	let confirmDelete = false;
	let relatedReports = 0;

	let hovering = false;
	let showOptions = false;
	let dragOver = false;

	let compareButton = false;
	let currentRequirementUpdating = false;

	let editingPriority = false;
	const priorities = ["soft", "hard"];
	let editingCategory = false;
	const categories = ["content", "structure", "presentation"];

	$: color = getCategoryColor(requirement.category, requirement.priority);

	let isEditing = false;

	function toggleEditingPriority() {
		editingPriority = !editingPriority;
	}

	function toggleEditingCategory() {
		editingCategory = !editingCategory;
	}

	function getCategoryColor(
		category: string | undefined,
		priority: string | undefined
	): string {
		let baseColor;

		if (suggested) {
			return "#f0f0f0"; // Grey for suggested requirements
		}

		if (category === "content") {
			baseColor = priority === "soft" ? "#FFEFE2" : "#FFDDC1"; // Lighter and regular colors for content
		} else if (category === "structure") {
			baseColor = priority === "soft" ? "#E3F2E9" : "#D1E7DD"; // Lighter and regular colors for structure
		} else if (category === "presentation") {
			baseColor = priority === "soft" ? "#E8F0FF" : "#CFE2FF"; // Lighter and regular colors for presentation
		} else {
			baseColor = "white"; // Default white
		}

		return baseColor;
	}

	function handlePriorityChange(newPriority) {
		if (requirement) {
			requirement.priority = newPriority;
			editingPriority = false; // Close the dropdown after selection
			color = getCategoryColor(requirement.category, newPriority);
		}
	}

	function handleCategoryChange(newCategory) {
		if (requirement) {
			requirement.category = newCategory;
			editingCategory = false; // Close the dropdown after selection
			color = getCategoryColor(newCategory, requirement.priority);
		}
	}
	let originalRequirement = JSON.parse(JSON.stringify(requirement));

	$: selected = false;

	function removeRequirement() {
		confirmDelete = false;
		relatedReports = 0;

		requirements.update((reqs) => {
			delete reqs[requirement.id];
			return reqs;
		});

		promptToUpdate.set(true);
	}
</script>

<div
	class=" cell parent
	{selected ? 'selected' : ''} 
	{compare ? 'compare-slice-cell' : ''}
	{compare && compareButton ? '' : 'pointer'}"
	style={suggested
		? `cursor:default; background: #f0f0f0;`
		: `cursor:default; background-color: ${color};`}
	draggable="true"
	on:mouseover={() => (hovering = true)}
	on:focus={() => (hovering = true)}
	on:mouseleave={() => (hovering = false)}
	on:blur={() => (hovering = false)}
	on:dragenter={() => (dragOver = true)}
	on:dragover={(ev) => ev.preventDefault()}
	on:dragleave={() => (dragOver = false)}
	on:dragstart={(ev) => {
		let transferData = JSON.stringify(requirement);
		ev.dataTransfer.setData("text/plain", transferData);
		ev.dataTransfer.dropEffect = "copy";
	}}
	on:drop={(ev) => {
		dragOver = false;
		const data = ev.dataTransfer.getData("text/plain");
		const example = JSON.parse(data);
		const exampleIds = requirement.examples.map((x) => x.id);
		if (!exampleIds.includes(example.id)) {
			requirement.examples.push(example);
		}
	}}>
	<!-- {#if showTooltip}
		<div class="tooltip-container">
			<div class="tooltip">
				{requirement.description}
			</div>
		</div>
	{/if} -->

	<div class="group" style:width="100%">
		<div class="group" style:width="100%">
			<div class="inline">
				<div class="hori-group" style:color="var(--G1)">
					{#if requirement.name !== ""}
						<RequirementChip
							name={requirement.name}
							id={requirement.id}
							{color} />
						<!-- <span class="category-tag">{requirement.category}</span> -->
						{#if editingCategory}
							<select
								class="dropdown"
								use:clickOutside
								on:click_outside={() => {
									editingCategory = false;
								}}
								bind:value={requirement.category}
								on:change={(event) => handleCategoryChange(event.target.value)}>
								{#each categories as category}
									<option value={category}>{category}</option>
								{/each}
							</select>
						{:else}
							<span
								class="category-tag"
								on:click={() => toggleEditingCategory()}>
								{requirement.category}
							</span>
						{/if}
						<!-- <span class="priority-tag">{requirement.priority}</span> -->
						{#if editingPriority}
							<select
								class="dropdown"
								use:clickOutside
								on:click_outside={() => {
									editingPriority = false;
								}}
								bind:value={requirement.priority}
								on:change={(event) => handlePriorityChange(event.target.value)}>
								{#each priorities as priority}
									<option value={priority}>{priority}</option>
								{/each}
							</select>
						{:else}
							<span
								class="priority-tag"
								on:click={() => toggleEditingPriority()}>
								{requirement.priority}
							</span>
						{/if}
					{/if}

					{#if currentRequirementUpdating}
						<CircularProgress
							style="height: 15px; width: 15px;"
							indeterminate />
					{/if}
					{#if requirement.mode && requirement.mode !== ""}
						<img
							class="tag"
							draggable="false"
							src="https://img.shields.io/badge/{requirement.mode === 'new'
								? 'new-green'
								: requirement.mode === 'deleted'
								? 'deleted-red'
								: 'edited-yellow'}"
							alt=""
							on:keydown={() => {}} />
						<TrailingIcon
							class="material-icons"
							style="margin-bottom: 5px; margin-left: 0px; cursor: pointer; color: #97ca00;"
							on:click={() => {
								requirements.update((reqs) => {
									reqs[requirement.id] = requirement;
									return reqs;
								});
								promptToUpdate.set(true);
							}}>
							check
						</TrailingIcon>
						<TrailingIcon
							class="material-icons"
							style="margin-bottom: 5px; margin-left: 3px; cursor: pointer; color: #e05d44;"
							on:click={() => {
								suggestedRequirements.update(($suggestRequirements) => {
									delete $suggestRequirements[requirement.id];
									return $suggestRequirements;
								});
							}}>
							close
						</TrailingIcon>
					{/if}

					<div
						class="description"
						style="background-color: {isEditing ? 'white' : color}"
						contenteditable={true}
						use:clickOutside
						on:click={() => {
							isEditing = true;
							if (requirement.description == "Write new requirements here...") {
								requirement.description = "";
							}
						}}
						on:input={(e) => {
							requirement.description = e.target.innerText;
							// requirements.update((reqs) => {
							// 	if (requirement.id in reqs) {
							// 		reqs[requirement.id] = requirement;
							// 	}
							// 	return reqs;
							// });
						}}
						on:blur={() => {
							// if (requirement.id in $requirements) {
							isEditing = false;
							if (requirement.description === "") {
								requirement.description = "Write new requirements here...";
								return;
							}
							if (requirement.description !== originalRequirement.description) {
								currentRequirementUpdating = true;
								ZenoService.optimizeRequirement({
									promptId: $currentPromptId,
									requirement: requirement,
								}).then((optimizedRequirement) => {
									requirement = optimizedRequirement;
									requirements.update((reqs) => {
										reqs[requirement.id] = requirement;
										return reqs;
									});
									currentRequirementUpdating = false;
								});
							}
							// }
						}}
						on:keydown={(e) => {
							if (e.key === "Enter") {
								e.preventDefault();
								e.target.blur();
							}
						}}>
						{requirement.description}
					</div>
				</div>
			</div>
			<div
				class="group"
				use:clickOutside
				on:click_outside={() => {
					showOptions = false;
				}}>
				{#if showOptions}
					<div id="options-container">
						<Paper style="padding: 3px 0px;" elevation={7}>
							<Content>
								<div
									class="option"
									on:keydown={() => ({})}
									on:click={(e) => {
										e.stopPropagation();
										showOptions = false;
										showNewSlice.set(false);
										showNewFolder.set(false);
										showSliceFinder.set(false);
										showNewRequirement.update((d) => !d);
										requirementToEdit.set(requirement);
									}}>
									<Icon style="font-size: 18px;" class="material-icons"
										>edit</Icon
									>&nbsp;
									<span>Edit</span>
								</div>
								<div
									class="option"
									on:keydown={() => ({})}
									on:click={(e) => {
										e.stopPropagation();
										showOptions = false;
										removeRequirement();
									}}>
									<Icon style="font-size: 18px;" class="material-icons"
										>delete_outline</Icon
									>&nbsp;
									<span>Remove</span>
								</div>
							</Content>
						</Paper>
					</div>
				{/if}
				<RequirementCellResult {compare} {requirement} />
				<!-- {#if compare}
						<RequirementCellResult {compare} {slice} sliceModel={$comparisonModel} />
					{/if} -->
				<div class="inline" style:cursor="pointer">
					<div
						style:width="36px"
						use:clickOutside
						on:click_outside={() => {
							hovering = false;
						}}>
						{#if suggested}
							<IconButton
								size="button"
								style="padding: 0px"
								on:click={(e) => {
									e.stopPropagation();
									suggestedRequirements.update(($reqs) => {
										delete $reqs[requirement.id];
										return $reqs;
									});
									requirements.update((reqs) => {
										reqs[requirement.id] = requirement;
										return reqs;
									});
									promptToUpdate.set(true);
								}}>
								<Icon component={Svg} viewBox="0 0 24 24">
									<path fill="green" d={mdiCheckOutline} />
								</Icon>
							</IconButton>
						{:else if hovering}
							<IconButton
								size="button"
								style="padding: 0px"
								on:click={(e) => {
									e.stopPropagation();
									showOptions = !showOptions;
								}}>
								<Icon component={Svg} viewBox="0 0 24 24">
									<path fill="black" d={mdiDotsHorizontal} />
								</Icon>
							</IconButton>
						{/if}
					</div>
				</div>
			</div>
		</div>
	</div>
</div>

<!-- <Dialog
	bind:open={confirmDelete}
	scrimClickAction=""
	escapeKeyAction=""
	aria-labelledby="delete-slice"
	aria-describedby="delete-slice">
	<Title id="simple-title">Delete Slice</Title>
	<Content id="simple-content"
		>This slice will be removed from {relatedReports} report{relatedReports > 1
			? "s"
			: ""}. Continue?</Content>
	<Actions>
		<Button
			on:click={() => {
				confirmDelete = false;
				relatedReports = 0;
			}}>
			<Label>No</Label>
		</Button>
		<Button use={[InitialFocus]} on:click={() => removeRequirement()}>
			<Label>Yes</Label>
		</Button>
	</Actions>
</Dialog> -->

<style>
	.tooltip-container {
		background: var(--G6);
		position: absolute;
		top: 100%;
		max-width: 1000px;
		width: fit-content;
		background: var(--G6);
		z-index: 10;
		left: 0px;
	}
	.tooltip {
		background: var(--G6);
		padding-left: 10px;
		padding-right: 10px;
		box-shadow: 1px 1px 3px 1px var(--G3);
		border-radius: 4px;
		padding-top: 10px;
		padding-bottom: 10px;
	}
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
	.compare-slice-cell {
		padding-top: 5px;
		padding-bottom: 5px;
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
	.pointer {
		cursor: pointer;
	}
	.selected {
		background: var(--P3);
	}
	.inline {
		display: flex;
		flex-direction: row;
	}
	.in-folder {
		margin-left: 35px;
		margin-top: 0px;
		margin-bottom: 0px;
	}
	#options-container {
		top: 0px;
		right: 0px;
		z-index: 10;
		position: absolute;
		margin-top: 35px;
	}
	.option {
		display: flex;
		flex-direction: row;
		align-items: center;
		cursor: pointer;
		width: 73px;
		padding: 1px 6px;
	}
	.option span {
		font-size: 12px;
	}
	.option:hover {
		background: var(--G5);
	}
	.description {
		font-size: normal;
		font-weight: lighter;
		cursor: text;
		margin-left: -5px;
		padding-left: 5px;
		padding-right: 5px;
	}

	.tag {
		cursor: default;
		margin-right: 2px;
		margin-bottom: -2.5px;
	}

	.category-tag {
		background-color: #c9d2ee; /* Example color for category tag */
		color: #333;
		padding: 2px 5px;
		border-radius: 3px;
		font-size: 0.8em;
		cursor: pointer;
	}

	.priority-tag {
		background-color: #f4f2b5; /* Example color for priority tag */
		color: #333;
		padding: 2px 5px;
		border-radius: 3px;
		font-size: 0.8em;
		cursor: pointer;
	}
	.dropdown {
		color: #333;
		padding: 2px 5px;
		border-radius: 3px;
		margin-bottom: 3px;
		font-size: 0.8em;
	}
</style>
