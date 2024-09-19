/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type EvaluatorFeedbackRequest = {
	model: string;
	promptId: string;
	exampleId: string;
	corrected_eval: boolean;
	requirementId: string;
};

