window.pdfPreview = {
    pdfDocs: {},
    currentPage: {},
    canvasIds: {},

    showPdf: function (url, canvasId) {
        this.canvasIds[url] = canvasId;
        if (!this.pdfDocs[url]) {
            var loadingTask = pdfjsLib.getDocument(url);
            loadingTask.promise.then((pdf) => {
                this.pdfDocs[url] = pdf;
                this.currentPage[url] = 1;
                this.renderPage(url, this.currentPage[url]);
            }, function (reason) {
                console.error(reason);
            });
        } else {
            this.renderPage(url, this.currentPage[url]);
        }
    },

    renderPage: function (url, pageNum) {
        this.pdfDocs[url].getPage(pageNum).then((page) => {
            var scale = 1.5;
            var viewport = page.getViewport({ scale: scale });

            var canvas = document.getElementById(this.canvasIds[url]);
            var context = canvas.getContext('2d');
            canvas.height = viewport.height;
            canvas.width = viewport.width;

            var renderContext = {
                canvasContext: context,
                viewport: viewport
            };
            page.render(renderContext);
        });
    },

    nextPage: function (url) {
        if (this.currentPage[url] >= this.pdfDocs[url].numPages) {
            return;
        }
        this.currentPage[url]++;
        this.renderPage(url, this.currentPage[url]);
    },

    prevPage: function (url) {
        if (this.currentPage[url] <= 1) {
            return;
        }
        this.currentPage[url]--;
        this.renderPage(url, this.currentPage[url]);
    },

    showButtons: function (id) {
        document.getElementById(id).style.display = "flex";
    },

    hideButtons: function (id) {
        document.getElementById(id).style.display = "none";
    }
};
