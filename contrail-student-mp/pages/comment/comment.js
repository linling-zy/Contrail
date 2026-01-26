Page({
    data: {
        isLoading: false,
        comment: ''
    },
    onLoad(options) {
        const comment = options && options.comment ? decodeURIComponent(options.comment) : ''
        this.setData({ comment })
    }
})
