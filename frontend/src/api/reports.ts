/**
 * Reports API service — no logic yet, stubs only.
 */
export const reportsApi = {
  list: (_orgId: number, _params?: { skip?: number; limit?: number }) => {
    // TODO: GET /reports?organization_id=...
    throw new Error('Not implemented')
  },

  getById: (_id: number) => {
    // TODO: GET /reports/:id
    throw new Error('Not implemented')
  },

  create: (_payload: unknown) => {
    // TODO: POST /reports
    throw new Error('Not implemented')
  },

  update: (_id: number, _payload: unknown) => {
    // TODO: PATCH /reports/:id
    throw new Error('Not implemented')
  },

  remove: (_id: number) => {
    // TODO: DELETE /reports/:id
    throw new Error('Not implemented')
  },
}

export default reportsApi
