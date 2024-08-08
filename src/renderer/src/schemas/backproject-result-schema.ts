import { object, string } from 'valibot'
import { baseParse } from './schema-helpers'

const BackprojectResultSchema = object({
	task_id: string('Task ID is required')
})

export const parseBackprojectResult = baseParse(
	BackprojectResultSchema,
	'Invalid backproject result'
)

export default BackprojectResultSchema
