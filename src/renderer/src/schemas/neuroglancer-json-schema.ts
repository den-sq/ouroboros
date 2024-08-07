import { array, InferOutput, object, safeParse, string } from 'valibot'

const NeuroglancerJSONSchema = object({
	layers: array(
		object({
			type: string('Type is required'),
			name: string('Name is required')
		})
	)
})

export type NeuroglancerJSON = InferOutput<typeof NeuroglancerJSONSchema>

export const parseNeuroglancerJSON = (
	jsonString: string | null
): { result: NeuroglancerJSON; error: string | null } => {
	const errorResult = { result: {} as NeuroglancerJSON, error: 'Invalid Neuroglancer JSON' }

	if (!jsonString || jsonString === '') return errorResult

	let parsedJSON = ''

	try {
		parsedJSON = JSON.parse(jsonString)
	} catch (e) {
		return errorResult
	}

	const jsonResult = safeParse(NeuroglancerJSONSchema, parsedJSON)

	if (jsonResult.success) {
		return { result: jsonResult.output, error: null }
	} else {
		return errorResult
	}
}

export default NeuroglancerJSONSchema
