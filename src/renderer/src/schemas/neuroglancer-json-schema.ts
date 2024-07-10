import { array, object, string } from 'valibot'

const NeuroglancerJSONSchema = object({
	layers: array(
		object({
			type: string('Type is required'),
			name: string('Name is required')
		})
	)
})

export default NeuroglancerJSONSchema
