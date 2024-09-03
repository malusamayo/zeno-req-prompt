<script lang="ts">
	import Button from "@smui/button";
	import Paper, { Content } from "@smui/paper";
	import type { Requirement } from "../../zenoservice";
	import { clickOutside } from "../../util/clickOutside";
	import { showNewRequirement, requirementToEdit } from "../../stores";

	let requirement: Requirement;
	let paperHeight;

	$: if ($showNewRequirement) {
		updateRequirement();
	}

	function updateRequirement() {
		if ($requirementToEdit) {
			requirement = JSON.parse(JSON.stringify($requirementToEdit));
		}
	}

	// TODO: handle updates / submit
</script>

<div
	id="paper-container"
	bind:clientHeight={paperHeight}
	use:clickOutside
	on:click_outside={() => {
		showNewRequirement.set(false);
		requirementToEdit.set(null);
	}}>
	<Paper
		elevation={7}
		class="paper"
		style="max-height: 75vh; {paperHeight &&
		paperHeight > window.innerHeight * 0.75
			? 'overflow-y: scroll'
			: 'overflow-y: show'}">
		<Content>
			<label>Name:</label>
			<input type="text" bind:value={requirement.name} />
			<label>Prompt Snippet:</label>
			<textarea bind:value={requirement.promptSnippet} />
			<label>Description:</label>
			<textarea bind:value={requirement.description} />
			<label>Evaluation Method:</label>
			<textarea
				bind:value={requirement.evaluationMethod}
				style="min-height: 120px;" />
			<div id="submit">
				<!-- <Button
					variant="outlined"
					on:click={createSlice}
					disabled={(!$sliceToEdit && $slices.has(sliceName)) ||
						($sliceToEdit &&
							originalName !== sliceName &&
							$slices.has(sliceName)) ||
						!isValidPredicates}>
					{$sliceToEdit ? "Update Slice" : "Create Slice"}
				</Button> -->
				<Button
					style="margin-right: 10px"
					variant="outlined"
					on:click={() => showNewRequirement.set(false)}>
					cancel
				</Button>
				<!-- {#if (!$sliceToEdit && $slices.has(sliceName)) || ($sliceToEdit && originalName !== sliceName && $slices.has(sliceName))}
					<p style:margin-right="10px" style:color="red">
						slice already exists
					</p>
				{/if} -->
			</div>
		</Content>
	</Paper>
</div>

<style>
	#paper-container {
		position: fixed;
		left: 580px;
		top: 70px;
		width: 400px;
		z-index: 20;
	}
	#submit {
		display: flex;
		flex-direction: row-reverse;
		align-items: center;
	}

	label {
		display: block;
		margin-top: 10px;
		padding-left: 10px; /* Adds space between the label and the window border */
	}

	input,
	textarea {
		width: calc(100% - 20px); /* Adjust width to account for padding */
		padding: 8px;
		margin-top: 5px;
		margin-left: 10px; /* Align inputs with labels */
		resize: none;
	}

	.close-button {
		display: block;
		margin: 20px auto 0 auto; /* Center the button horizontally and add margin at the top */
		padding: 10px 20px;
		background-color: #f0f0f0;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}

	.close-button:hover {
		background-color: #e0e0e0; /* Slightly darker background on hover */
	}
</style>
