import { BaseIssue, BaseSchema, InferOutput, safeParse } from 'valibot'

export type Schema = BaseSchema<unknown, unknown, BaseIssue<unknown>>

export type ParseResult<T> = {
	result: T
	error: string | null
}

export function makeErrorResult<T>(error: string): ParseResult<T> {
	return { result: {} as T, error }
}

export function makeSuccessResult<T>(result: T): ParseResult<T> {
	return { result, error: null }
}

export function baseParse<T extends Schema>(
	schema: T,
	errorMessage: string
): (input: object | null) => ParseResult<InferOutput<T>> {
	return (input: object | null) => {
		const { success, output } = safeParse(schema, input)

		if (success) {
			return makeSuccessResult(output)
		} else {
			return makeErrorResult(errorMessage)
		}
	}
}
