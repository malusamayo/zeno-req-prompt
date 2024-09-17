/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type Example = {
	id: string;
	input: string;
	output: string;
	isPositive: boolean;
	feedback: string;
};

export type Requirement = {
	id: string;
	name: string;
	description: string;
	promptSnippet: string;
	evaluationMethod: string;
	examples?: Array<Example>;
	mode?: string;
};

export type Prompt = {
	text: string;
	version: string;
	requirements: { [id: string]: Requirement };
};

// Utility function to compare arrays of Examples
function areExamplesEqual(
	examples1?: Array<Example>,
	examples2?: Array<Example>
): boolean {
	if (!examples1 && !examples2) return true;
	if (!examples1 || !examples2) return false;
	if (examples1.length !== examples2.length) return false;

	// Compare each element in the array
	for (let i = 0; i < examples1.length; i++) {
		const example1 = examples1[i];
		const example2 = examples2[i];
		if (
			example1.id !== example2.id ||
			example1.input !== example2.input ||
			example1.output !== example2.output ||
			example1.isPositive !== example2.isPositive ||
			example1.feedback !== example2.feedback
		) {
			return false;
		}
	}
	return true;
	[];
}

// Function to compare two Requirement objects for equality
export function areRequirementsEqual(
	req1: Requirement,
	req2: Requirement
): boolean {
	return (
		req1.id === req2.id &&
		req1.name === req2.name &&
		req1.description === req2.description &&
		req1.promptSnippet === req2.promptSnippet &&
		req1.evaluationMethod === req2.evaluationMethod &&
		req1.mode === req2.mode &&
		areExamplesEqual(req1.examples, req2.examples)
	);
}
