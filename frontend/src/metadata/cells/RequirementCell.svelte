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
		requirementUpdating
	} from "../../stores";
	import { clickOutside } from "../../util/clickOutside";
	import { ZenoService, type Slice, type Requirement, type Example} from "../../zenoservice";
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

	let draggedexample = null;
	let showdraggingoptions = false;

	$: color = getCategoryColor(requirement.category, requirement.priority);

	let isEditing = false;

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

	// function feedbackToRequirements(feedbackPositive) {
    //     requirementUpdating.set(true);
    //     ZenoService.updateReqFeedback({
    //         model: $model,
    //         promptId: $currentPromptId,
    //         exampleId: String(draggedexample.id),
    //         isPositive: feedbackPositive,
    //         feedback: '',
    //         requirementId: requirement.id,
    //     }).then((newRequirements) => {
    //         requirements.set(newRequirements);
    //         requirementUpdating.set(false);
    //     })
    // }

	function feedbackToEvaluators() {
		requirementUpdating.set(true);
		ZenoService.evaluatorUpdates({
			model: $model,
			promptId: $currentPromptId,
			exampleId: String(draggedexample.id),
			corrected_eval: !draggedexample.isPositive,
			requirementId: requirement.id,
		}).then((newRequirements) => {
			requirements.set(newRequirements);
			requirementUpdating.set(false);
		});
	}

	function handlexampledrag(isFix, isPositive){
		if (isFix) {
			feedbackToEvaluators();
		}
		else{
			draggedexample.isPositive = isPositive;
			let feedbackPositive = 'negative';
			if (isPositive){
				feedbackPositive = 'positive';
			}
			draggedexample.feedback = `This is a '${feedbackPositive}' example affirmed by users.`;
			requirement.examples.push(draggedexample);
		}
		showdraggingoptions = false;
	}

	function isExample(obj: any): obj is Example {
		return (
			typeof obj === 'object' &&
			obj !== null &&
			typeof obj.id === 'string' &&
			typeof obj.input === 'string' &&
			typeof obj.output === 'string' &&
			typeof obj.isPositive === 'boolean' &&
			typeof obj.feedback === 'string'
		);
	}
</script>

<div
	class=" cell parent
	{selected ? 'selected' : ''} 
	{compare ? 'compare-slice-cell' : ''}
	{compare && compareButton ? '' : 'pointer'}"
	style={suggested
		? `cursor:default; background: #f0f0f0;`
		: `cursor:default; `}
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
		ev.preventDefault();
		dragOver = false;
		
		const data = ev.dataTransfer.getData("text/plain");
		const example = JSON.parse(data);

		if (isExample(example)) {
			const exampleIds = requirement.examples.map((x) => x.id);
		
			if (!exampleIds.includes(example.id)) {
				draggedexample = example;
				showdraggingoptions = true;
			}
		}
		else{
			console.log(example);
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
						<RequirementChip name={requirement.name} id={requirement.id} />
						{#if showdraggingoptions}
							<div class="modal" 
							use:clickOutside
							on:click_outside={() => (showdraggingoptions = false)}>
								<div class="modal-content">
									<div class="icon-container">
										<div class="icon-item">
											<span class="material-icons" style="color: green;"on:click={() => handlexampledrag(false,true)}> thumb_up</span>
											<p class="caption">Positive example</p>
										</div>
										<div class="icon-item">
											<span class="material-icons" style="color: red;"on:click={() => handlexampledrag(false,false)}>thumb_down</span>
											<p class="caption">Negative example</p>
										</div>
										<div class="icon-item">
											<span class="material-icons" style="color: black;"on:click={() => handlexampledrag(true,true)}>build</span>
											<p class="caption">Fix evaluator</p>
										</div>
									</div>
									
								</div>
							</div>
						{/if}
						<!-- <span class="category-tag">{requirement.category}</span> -->
						<div class="dropdown-container">
							<span
								class="category-tag"
								style="background-color:{color}"
								on:click={() => {
									editingCategory = !editingCategory;
								}}
								on:keydown={() => {}}>
								{requirement.category}
							</span>
							<div
								class="group"
								use:clickOutside
								on:click_outside={() => {
									editingCategory = false;
								}}>
								{#if editingCategory}
									<div id="dropdown-container">
										<Paper style="padding: 3px 0px;" elevation={7}>
											<Content>
												{#each categories as category}
													<div
														class="option"
														on:click={() => handleCategoryChange(category)}
														on:keydown={(e) => {
															if (e.key === "Enter") {
																e.preventDefault();
																handleCategoryChange(category);
															}
														}}>
														<span>{category}</span>
													</div>
												{/each}
											</Content>
										</Paper>
									</div>
								{/if}
							</div>
						</div>

						<div class="dropdown-container">
							<span
								class="priority-tag"
								style="background-color:{color}"
								on:click={() => {
									editingPriority = !editingPriority;
								}}
								on:keydown={() => {}}>
								{requirement.priority}
							</span>
							<div
								class="group"
								use:clickOutside
								on:click_outside={() => {
									editingPriority = false;
								}}>
								{#if editingPriority}
									<div id="dropdown-container">
										<Paper style="padding: 0px" elevation={7}>
											<Content>
												{#each priorities as priority}
													<div
														class="option"
														style="width:30px;"
														on:click={() => handlePriorityChange(priority)}
														on:keydown={(e) => {
															if (e.key === "Enter") {
																e.preventDefault();
																handlePriorityChange(priority);
															}
														}}>
														<span>{priority}</span>
													</div>
												{/each}
											</Content>
										</Paper>
									</div>
								{/if}
							</div>
						</div>
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
		padding: 0px 6px;
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

	.dropdown-container {
		position: relative;
		display: inline-block;
	}

	#dropdown-container {
		top: 0px;
		right: 0px;
		z-index: 10;
		position: absolute;
		margin-top: 18px;
	}
	.modal {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 300px;
		padding: 20px;
		background-color: white;
		border: 1px solid #ccc;
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
		z-index: 100;
	}

	.modal-content {
		display: flex;
		flex-direction: column;
	}
	.icon-container {
		display: flex;
		gap: 10px; /* Adjust spacing between icons as needed */
		align-items: center; /* Vertically center the icons if they vary in height */
	}

	.material-icons {
		cursor: pointer; /* Optional: Adds a pointer cursor for interactivity */
		font-size: 24px; /* Adjust size as desired */
	}
	.caption {
		margin-top: 4px; /* Space between icon and caption */
		font-size: 12px; /* Adjust caption font size */
		text-align: center;
		color: #333; /* Adjust caption color */
		font-weight: bold;
	}
	.icon-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
	}
</style>
