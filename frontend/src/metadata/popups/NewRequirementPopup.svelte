<script lang="ts">
	import Button from "@smui/button";
	import Paper, { Content } from "@smui/paper";
	import type { Requirement } from "../../zenoservice";
	import { clickOutside } from "../../util/clickOutside";
	import { showNewRequirement, requirementToEdit } from "../../stores";
	import Textfield from "@smui/textfield";

	let requirement: Requirement;
	let paperHeight;
	let nameInput;

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
			<Textfield
				label="Requirement Name"
				bind:value={requirement.name}
				bind:this={nameInput} />
			<label>Description</label>
			<textarea bind:value={requirement.description} />
			<label>Evaluation Method</label>
			<textarea
				bind:value={requirement.evaluationMethod}
				style="min-height: 120px;" />
			<label>Prompt Snippet</label>
			<textarea bind:value={requirement.promptSnippet} />
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
	}

	input,
	textarea {
		width: calc(100% - 20px); /* Adjust width to account for padding */
		padding: 8px;
		resize: none;
	}
</style>
