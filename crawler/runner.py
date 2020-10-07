import os, time, threading

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from crawler.mde_crawler import mde_crawler

class CRAWLER:
    def __init__(self, db):
        # initialize arrays
        self.active_links = db.read_table("active_links")
        self.listings_links = db.read_table("listings_links")
        self.processed_links = db.read_table("processed_links")

        # start the database updater thread
        self.running = True
        db_thread = threading.Thread(target=self.database_updater, args=(db, ))
        db_thread.start()

        # start the live graph in a separate thread
        graph_thread = threading.Thread(target=self.live_graph, args=())
        graph_thread.start()

        # start mobile.de_crawler
        mde_crawler_thread = threading.Thread(target=mde_crawler, args=(self, ))
        mde_crawler_thread.start()

        try:
            while True:
                stopper = input("Type S or STOP to interrupt the execution.\n")
                if "s" in stopper.lower():
                    raise KeyboardInterrupt
        except KeyboardInterrupt:
            print("Interruption detected, this might take up to 45 seconds.")
            self.running = False
            mde_crawler_thread.join()
            db_thread.join()
            os._exit(0)

    # turn list into tuples
    def tuplify(self, data: list):
        return [(d,) for d in data]

    # limit graph array size
    def limit_size(self, array: list, item) -> None:
        LIST_SIZE = 200
        array.append(item)
        if len(array) == LIST_SIZE:
            array.pop(0)

    # database updater thread
    def database_updater(self, db) -> None:
        while True:
            time.sleep(30)
            db.rewrite_table_values("active_links", self.tuplify(self.active_links))
            db.rewrite_table_values("listings_links", self.tuplify(self.listings_links))
            db.rewrite_table_values("processed_links", self.tuplify(self.processed_links))
            if self.running == False:
                break

    # generate the live graph
    def live_graph(self):
        plt.style.use("dark_background")
        fig, (links_plot, perf_plot) = plt.subplots(2)
        fig.canvas.set_window_title("Crawler Activity Visualizer")

        # timestamps = []
        # try:
        #    timestamps.append(time.time() - timestamps[-1])
        # except IndexError:
        #    timestamps.append(time.time())

        # performance plot data
        self.interval_processed = []

        # al - active links
        # pl - processed links
        # lu - listings rewrite_table_values
        self.al_history = []
        self.pl_history = []
        self.lu_history = []

        def animate(i):
            # links plot
            self.limit_size(self.al_history, len(self.active_links))
            self.limit_size(self.pl_history, len(self.processed_links))
            self.limit_size(self.lu_history, len(self.listings_links))

            links_plot.clear()
            links_plot.plot(
                self.pl_history, self.al_history, label="Active links", color="#f4a261"
            )
            links_plot.plot(
                self.pl_history,
                self.lu_history,
                label="Nr. of listings",
                color="#2a9d8f",
            )
            links_plot.set_title("")
            links_plot.set_xlabel("Processed links")
            links_plot.set_ylabel("Number of urls")
            links_plot.legend()

            # performance plot
            try:
                self.limit_size(
                    self.interval_processed, self.pl_history[-1] - self.pl_history[-2]
                )
            except IndexError:
                self.limit_size(self.interval_processed, 0)
            perf_plot.clear()
            perf_plot.plot(
                self.pl_history,
                self.interval_processed,
                label="Interval",
                color="#e9c46a",
            )
            perf_plot.set_title("Crawler performance")
            perf_plot.set_xlabel("Number of processed links")
            perf_plot.set_ylabel("Processed per iterations")
            perf_plot.legend()

        anim = animation.FuncAnimation(fig, animate, interval=1000)
        plt.show()
