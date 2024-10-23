<script lang="ts">
	import InstanceView from "./instance-views/InstanceView.svelte";
	import MetadataPanel from "./metadata/MetadataPanel.svelte";
	import NewFolderPopup from "./metadata/popups/NewFolderPopup.svelte";
	import NewSlicePopup from "./metadata/popups/NewSlicePopup.svelte";
	import SliceFinderPopup from "./metadata/popups/SliceFinderPopup.svelte";
	import NewTagPopup from "./metadata/popups/NewTagPopup.svelte";
	import {
		ready,
		showNewFolder,
		showNewSlice,
		showSliceFinder,
		showNewTag,
		status,
		showNewRequirement,
	} from "./stores";
	import NewRequirementPopup from "./metadata/popups/NewRequirementPopup.svelte";
	import RequirementPanel from "./metadata/RequirementPanel.svelte";
	import TaskView from "./metadata/TaskView.svelte";
</script>

{#if $ready && $status.completeColumns.length > 0}
	<!-- These popups are at the top level b/c of issues with overflow-y scroll. -->
	{#if $showNewSlice}
		<NewSlicePopup />
	{/if}
	{#if $showNewFolder}
		<NewFolderPopup />
	{/if}
	{#if $showSliceFinder}
		<SliceFinderPopup />
	{/if}
	{#if $showNewTag}
		<NewTagPopup />
	{/if}
	{#if $showNewRequirement}
		<NewRequirementPopup />
	{/if}
	<div class="container">
		<!-- <MetadataPanel /> -->
		<TaskView />
		<!-- <div id="samples">
			<InstanceView />
		</div> -->
	</div>
{/if}

<style>
	#samples {
		width: 100%;
		margin-right: 20px;
		margin-left: 20px;
	}
	.container {
		display: flex;
		justify-content: center; /* Centers horizontally */
		align-items: center; /* Centers vertically */
		height: 100vh; /* Full viewport height */
	}
</style>
