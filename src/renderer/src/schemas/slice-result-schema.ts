import { object, string } from 'valibot'

const SliceResultSchema = object({
	task_id: string('Task ID is required')
})

export default SliceResultSchema
