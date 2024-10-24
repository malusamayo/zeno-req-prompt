/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ColorsProjectRequest } from "../models/ColorsProjectRequest";
import type { EmbedProject2DRequest } from "../models/EmbedProject2DRequest";
import type { EntryRequest } from "../models/EntryRequest";
import type { GroupMetric } from "../models/GroupMetric";
import type { HistogramBucket } from "../models/HistogramBucket";
import type { HistogramRequest } from "../models/HistogramRequest";
import type { MetricRequest } from "../models/MetricRequest";
import type { PlotRequest } from "../models/PlotRequest";
import type { Points2D } from "../models/Points2D";
import type { PointsColors } from "../models/PointsColors";
import type { Report } from "../models/Report";
import type { Slice } from "../models/Slice";
import type { SliceFinderRequest } from "../models/SliceFinderRequest";
import type { SliceFinderReturn } from "../models/SliceFinderReturn";
import type { StringFilterRequest } from "../models/StringFilterRequest";
import type { TableRequest } from "../models/TableRequest";
import type { Tag } from "../models/Tag";
import type { TagMetricKey } from "../models/TagMetricKey";
import type { ZenoColumn } from "../models/ZenoColumn";
import type { ZenoSettings } from "../models/ZenoSettings";
import type { ZenoVariables } from "../models/ZenoVariables";
import type {UpdateFeedbackRequest} from "../models/UpdateFeedbackRequest";
import type {SuggestNewReqRequest} from "../models/SuggestNewReqRequest";
import type {RemoveExampleFeedback} from "../models/RemoveExample";
import type {
	FeedbackRequest,
	InferenceRequest,
	Prompt,
	Requirement,
	EvaluatorFeedbackRequest,
} from "..";

import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";

export class ZenoService {
	/**
	 * Get Settings
	 * @returns ZenoSettings Successful Response
	 * @throws ApiError
	 */
	public static getSettings(): CancelablePromise<ZenoSettings> {
		return __request(OpenAPI, {
			method: "GET",
			url: "/settings",
		});
	}

	/**
	 * Get Complete Columns
	 * @returns ZenoSettings Successful Response
	 * @throws ApiError
	 */
	public static getCompleteColumns(): CancelablePromise<ZenoColumn[]> {
		return __request(OpenAPI, {
			method: "GET",
			url: "/complete-columns",
		});
	}

	/**
	 * Get Initial Info
	 * @returns ZenoVariables Successful Response
	 * @throws ApiError
	 */
	public static getInitialInfo(): CancelablePromise<ZenoVariables> {
		return __request(OpenAPI, {
			method: "GET",
			url: "/initialize",
		});
	}

	/**
	 * Get Slices
	 * @returns Slice Successful Response
	 * @throws ApiError
	 */
	public static getSlices(): CancelablePromise<Record<string, Slice>> {
		return __request(OpenAPI, {
			method: "GET",
			url: "/slices",
		});
	}

	/**
	 * Get Tags
	 * @returns Tag Successful Response
	 * @throws ApiError
	 */
	public static getTags(): CancelablePromise<Record<string, Tag>> {
		return __request(OpenAPI, {
			method: "GET",
			url: "/tags",
		});
	}

	/**
	 * Get Reports
	 * @returns Report Successful Response
	 * @throws ApiError
	 */
	public static getReports(): CancelablePromise<Array<Report>> {
		return __request(OpenAPI, {
			method: "GET",
			url: "/reports",
		});
	}

	/**
	 * Get Prompts
	 * @returns Report Successful Response
	 * @throws ApiError
	 */
	public static getPrompts(): CancelablePromise<Record<string, Prompt>> {
		return __request(OpenAPI, {
			method: "GET",
			url: "/prompts",
		});
	}

	/**
	 * Get Current Prompt Version
	 * @returns Report Successful Response
	 * @throws ApiError
	 */
	public static getCurrentPromptId(): CancelablePromise<Array<string>> {
		return __request(OpenAPI, {
			method: "GET",
			url: "/prompt-version",
		});
	}

	/**
	 * Create New Prompt
	 * @param requestBody
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static createNewPrompt(
		requestBody: Prompt
	): CancelablePromise<Array<Prompt>> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/prompt",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Run Prompt on Data
	 * @param requestBody
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static runPrompt(
		requestBody: InferenceRequest
	): CancelablePromise<any> {
		console.log(requestBody);
		return __request(OpenAPI, {
			method: "POST",
			url: "/run-prompt",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Optimize one requirement
	 * @param requestBody
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static optimizeRequirement(
		requestBody: Array<Requirement>
	): CancelablePromise<Requirement> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/optimize-requirement",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * update evaluator
	 * @param requestBody
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static evaluatorUpdates(
		requestBody: EvaluatorFeedbackRequest
	): CancelablePromise<Record<string, Requirement>> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/evaluator-updates",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Suggest requirement updates
	 * @param requestBody
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static suggestRequirementUpdates(
		requestBody: FeedbackRequest
	): CancelablePromise<Record<string, Requirement>> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/suggest-requirement-updates",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Suggest requirement updates
	 * @param requestBody
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static updateReqFeedback(
		requestBody: UpdateFeedbackRequest
	): CancelablePromise<Record<string, Requirement>> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/update-requirement-feedback",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	public static removeExample(
		requestBody: RemoveExampleFeedback
	): CancelablePromise<Record<string, Requirement>> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/remove-example",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Suggest requirements
	 * @param requestBody
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static suggestRequirements(requestBody: SuggestNewReqRequest): CancelablePromise<
		Record<string, Requirement>
	> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/suggest-requirements",
			mediaType: "application/json",
			body: requestBody,
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Update Reports
	 * @param requestBody
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static updateReports(
		requestBody: Array<Report>
	): CancelablePromise<any> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/reports",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Set Folders
	 * @param requestBody
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static setFolders(requestBody: Array<string>): CancelablePromise<any> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/folders",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Get Filtered Ids
	 * @param requestBody
	 * @returns string Successful Response
	 * @throws ApiError
	 */
	public static getFilteredIds(
		requestBody: PlotRequest
	): CancelablePromise<string> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/filtered-ids",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Get Filtered Table
	 * @param requestBody
	 * @returns string Successful Response
	 * @throws ApiError
	 */
	public static getFilteredTable(
		requestBody: TableRequest
	): CancelablePromise<string> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/filtered-table",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Refresh Data
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static refreshData(): CancelablePromise<any> {
		return __request(OpenAPI, {
			method: "GET",
			url: "/refresh",
		});
	}

	/**
	 * Get Histogram Buckets
	 * @param requestBody
	 * @returns HistogramBucket Successful Response
	 * @throws ApiError
	 */
	public static getHistogramBuckets(
		requestBody: Array<ZenoColumn>
	): CancelablePromise<Array<Array<HistogramBucket>>> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/histograms",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Calculate Histogram Counts
	 * @param requestBody
	 * @returns number Successful Response
	 * @throws ApiError
	 */
	public static calculateHistogramCounts(
		requestBody: HistogramRequest
	): CancelablePromise<Array<Array<number>>> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/histogram-counts",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Calculate Histogram Metrics
	 * @param requestBody
	 * @returns number Successful Response
	 * @throws ApiError
	 */
	public static calculateHistogramMetrics(
		requestBody: HistogramRequest
	): CancelablePromise<Array<Array<number>>> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/histogram-metrics",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Create New Tag
	 * @param requestBody
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static createNewTag(requestBody: Tag): CancelablePromise<any> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/tag",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Delete Tag
	 * @param requestBody
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static deleteTag(requestBody: Array<string>): CancelablePromise<any> {
		return __request(OpenAPI, {
			method: "DELETE",
			url: "/tag",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Create New Slice
	 * @param requestBody
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static createNewSlice(requestBody: Slice): CancelablePromise<any> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/slice",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Delete Slice
	 * @param requestBody
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static deleteSlice(
		requestBody: Array<string>
	): CancelablePromise<any> {
		return __request(OpenAPI, {
			method: "DELETE",
			url: "/slice",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Filter String Metadata
	 * @param requestBody
	 * @returns string Successful Response
	 * @throws ApiError
	 */
	public static filterStringMetadata(
		requestBody: StringFilterRequest
	): CancelablePromise<Array<string>> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/string-filter",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Get Metrics For Slices
	 * @param requestBody
	 * @returns GroupMetric Successful Response
	 * @throws ApiError
	 */
	public static getMetricsForSlices(
		requestBody: MetricRequest
	): CancelablePromise<Array<GroupMetric>> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/slice-metrics",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Get Metrics For Slices And Tags
	 * @param requestBody
	 * @returns GroupMetric Successful Response
	 * @throws ApiError
	 */
	public static getMetricsForSlicesAndTags(
		requestBody: MetricRequest
	): CancelablePromise<Array<GroupMetric>> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/slice-tag-metrics",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Get Metrics For Tags
	 * @param requestBody
	 * @returns GroupMetric Successful Response
	 * @throws ApiError
	 */
	public static getMetricsForTags(
		requestBody: Array<TagMetricKey>
	): CancelablePromise<Array<GroupMetric>> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/tag-metrics",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Embed Exists
	 * Checks if embedding exists for a model.
	 * Returns the boolean True or False directly
	 * @param model
	 * @returns boolean Successful Response
	 * @throws ApiError
	 */
	public static embedExists(model: string): CancelablePromise<boolean> {
		return __request(OpenAPI, {
			method: "GET",
			url: "/embed-exists/{model}",
			path: {
				model: model,
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Project Embed Into 2D
	 * @param requestBody
	 * @returns Points2D Successful Response
	 * @throws ApiError
	 */
	public static projectEmbedInto2D(
		requestBody: EmbedProject2DRequest
	): CancelablePromise<Points2D> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/embed-project",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Run Slice Finder
	 * @param requestBody
	 * @returns SliceFinderReturn Successful Response
	 * @throws ApiError
	 */
	public static runSliceFinder(
		requestBody: SliceFinderRequest
	): CancelablePromise<SliceFinderReturn> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/slice-finder",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Get Projection Colors
	 * @param requestBody
	 * @returns PointsColors Successful Response
	 * @throws ApiError
	 */
	public static getProjectionColors(
		requestBody: ColorsProjectRequest
	): CancelablePromise<PointsColors> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/colors-project",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Get Df Row Entry
	 * @param requestBody
	 * @returns string Successful Response
	 * @throws ApiError
	 */
	public static getDfRowEntry(
		requestBody: EntryRequest
	): CancelablePromise<string> {
		return __request(OpenAPI, {
			method: "POST",
			url: "/entry",
			body: requestBody,
			mediaType: "application/json",
			errors: {
				422: `Validation Error`,
			},
		});
	}
}
