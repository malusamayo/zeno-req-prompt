/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type UpdateFeedbackRequest = {
	model: string;
	promptId: string;
	exampleId: string;
	isPositive: boolean;
	feedback: string;
    requirementId: string;
};
