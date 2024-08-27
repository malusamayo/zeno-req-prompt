/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type Requirement = {
	id: string;
	name: string;
	description: string;
	promptSnippet: string;
	evaluationMethod: string;
};

export type Prompt = {
	text: string;
	version: string;
	requirements: Requirement[];
};
