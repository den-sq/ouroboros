import { object, string } from 'valibot'
import { baseParse } from './schema-helpers'

const SliceResultSchema = object({
	task_id: string('Task ID is required')
})

export const parseSliceResult = baseParse(SliceResultSchema, 'Invalid slice result')

export default SliceResultSchema
