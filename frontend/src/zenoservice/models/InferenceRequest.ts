/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { FilterIds } from "./FilterIds";

export type InferenceRequest = {
	model: string;
	promptId: string;
	filterIds?: FilterIds;
};
