import type {
	FilterIds,
	FilterPredicateGroup,
	ZenoColumn,
} from "../zenoservice";
import { ZenoService } from "../zenoservice/";
import { ZenoColumnType } from "./../zenoservice/models/ZenoColumnType";
import { setModelForFilterPredicateGroup } from "./slice";

export async function getFilteredTable(
	completeColumns,
	filterModels: string[],
	promptIds: string[],
	diffColumn: ZenoColumn,
	filterPredicates: FilterPredicateGroup,
	sliceRange: [number, number],
	sort: [ZenoColumn | string, boolean],
	tagIds: FilterIds,
	filterIds?: FilterIds,
	tagList?: Array<string>
) {
	const requestedColumns = completeColumns.filter(
		(c) =>
			c.columnType !== ZenoColumnType.EMBEDDING &&
			(filterModels.includes(c.model) || c.model === "") &&
			(promptIds.includes(c.promptId) || c.promptId === "")
	);

	// create diff columns for comparison view
	let diffColumn1 = undefined;
	let diffColumn2 = undefined;
	if (diffColumn) {
		diffColumn1 = Object.assign({}, diffColumn);
		diffColumn2 = Object.assign({}, diffColumn);
		const addModel = [
			ZenoColumnType.POSTDISTILL,
			ZenoColumnType.OUTPUT,
		].includes(diffColumn.columnType);
		diffColumn1.model = addModel ? filterModels[0] : "";
		diffColumn2.model = addModel ? filterModels[1] : "";
	}

	const res = await ZenoService.getFilteredTable({
		columns: requestedColumns,
		diffColumn1,
		diffColumn2,
		filterPredicates,
		sliceRange,
		sort,
		tagIds,
		filterIds,
		tagList,
	});
	return JSON.parse(res);
}

/**
 * Gets a list of ids from the filter predicates only
 */
export async function getFilteredIds(
	filterPredicates: FilterPredicateGroup,
	model: string,
	tagIds: FilterIds = { ids: [] }
) {
	const res = await ZenoService.getFilteredIds({
		filterPredicates: setModelForFilterPredicateGroup(filterPredicates, model),
		tagIds,
	});
	return JSON.parse(res);
}
