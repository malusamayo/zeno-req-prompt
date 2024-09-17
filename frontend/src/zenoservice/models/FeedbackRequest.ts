/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type FeedbackRequest = {
	model: string;
	promptId: string;
	exampleId: string;
	isPositive: boolean;
	feedback: string;
};
