<script lang="ts">
	import { requirements, requirementToEdit } from "../../stores";

	export let content;
	export let id;

	let isHighlighted: boolean = false;
	let requirement;

	$: {
		name;
		requirement = $requirements[id];
	}

	$: {
		$requirementToEdit;
		isHighlighted = $requirementToEdit && $requirementToEdit.id === id;
	}
</script>

<span class:highlighted={isHighlighted ? "highlighted" : ""}>
	{content}
</span>

<style>
	.highlighted {
		background-color: #fccde5;
	}
</style>
